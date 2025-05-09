package com.example.drools;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.kie.api.KieServices;
import org.kie.api.builder.KieBuilder;
import org.kie.api.builder.KieFileSystem;
import org.kie.api.builder.KieModule;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;

class DroolsTest {

    private KieSession getKieSession() {
        // Получаем KieServices
        KieServices kieServices = KieServices.Factory.get();

        // Создаём KieFileSystem для явной загрузки ресурсов
        KieFileSystem kieFileSystem = kieServices.newKieFileSystem();

        // Добавляем kmodule.xml
        String kmoduleContent = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
                                "<kmodule xmlns=\"http://www.drools.org/xsd/kmodule\">\n" +
                                "    <kbase name=\"rules\" packages=\"rules\">\n" +
                                "        <ksession name=\"defaultKieSession\" default=\"true\"/>\n" +
                                "    </kbase>\n" +
                                "</kmodule>";
        kieFileSystem.write("src/main/resources/META-INF/kmodule.xml", kmoduleContent);

        // Добавляем rules.drl
        String rulesContent = "package rules;\n" +
                             "\n" +
                             "import com.example.drools.Patient;\n" +
                             "\n" +
                             "rule \"Критическое состояние - Нестабильные витальные\"\n" +
                             "    salience 20\n" +
                             "    when\n" +
                             "        $p : Patient( (systolicBPSet == true && systolicBP < 90.0) || (heartRateSet == true && heartRate > 110.0),\n" +
                             "                       diagnosis == null )\n" +
                             "    then\n" +
                             "        System.out.println(\"Правило сработало: Критическое состояние с признаками нестабильности (АД < 90 или ЧСС > 110).\");" +
                             "        modify($p) { setDiagnosis(\"Критическое состояние (шок/аритмия)\") };\n" +
                             "end\n" +
                             "\n" +
                             "rule \"Высокий риск ОКС - Классические признаки\"\n" +
                             "    salience 15\n" +
                             "    when\n" +
                             "        $p : Patient( chestPainSet == true, chestPain == true,\n" +
                             "                      ecgAbnormalSet == true, ecgAbnormal == true,\n" +
                             "                      troponinHighSet == true, troponinHigh == true,\n" +
                             "                      diagnosis == null )\n" +
                             "    then\n" +
                             "        System.out.println(\"Правило сработало: Высокий риск ОКС.\");" +
                             "        modify($p) { setDiagnosis(\"Высокий риск ОКС\") };\n" +
                             "end\n" +
                             "\n" +
                             "rule \"Низкий риск ОКС - Классические признаки\"\n" +
                             "    salience 10\n" +
                             "    when\n" +
                             "        $p : Patient( chestPainSet == true, chestPain == true,\n" +
                             "                      ecgAbnormalSet == true, ecgAbnormal == false,\n" +
                             "                      troponinHighSet == true, troponinHigh == false,\n" +
                             "                      (systolicBPSet == false || systolicBP >= 90.0),\n" +
                             "                      (heartRateSet == false || heartRate <= 110.0),\n" +
                             "                      diagnosis == null )\n" +
                             "    then\n" +
                             "        System.out.println(\"Правило сработало: Низкий риск ОКС.\");" +
                             "        modify($p) { setDiagnosis(\"Низкий риск ОКС\") };\n" +
                             "end\n" +
                             "\n" +
                             "rule \"Подозрение на ОКС - Неполные данные\"\n" +
                             "    salience 5\n" +
                             "    when\n" +
                             "         $p : Patient( chestPainSet == true, chestPain == true,\n" +
                             "                       (ecgAbnormalSet == false || troponinHighSet == false),\n" +
                             "                       (systolicBPSet == false || systolicBP >= 90.0),\n" +
                             "                       (heartRateSet == false || heartRate <= 110.0),\n" +
                             "                       diagnosis == null )\n" +
                             "    then\n" +
                             "        System.out.println(\"Правило сработало: Подозрение на ОКС при неполных данных.\");" +
                             "        modify($p) { setDiagnosis(\"Подозрение на ОКС, требуются ЭКГ и тропонин\") };\n" +
                             "end\n" +
                             "\n" +
                             "rule \"Неопределённый диагноз\"\n" +
                             "    salience -10\n" +
                             "    when\n" +
                             "        $p : Patient( diagnosis == null )\n" +
                             "    then\n" +
                             "        System.out.println(\"Правило сработало: Не удалось определить диагноз.\");" +
                             "        modify($p) { setDiagnosis(\"Не удалось определить диагноз\") };\n" +
                             "end";
        kieFileSystem.write("src/main/resources/rules/rules.drl", rulesContent);

        // Создаём KieModule
        KieBuilder kieBuilder = kieServices.newKieBuilder(kieFileSystem);
        kieBuilder.buildAll();
        KieModule kieModule = kieBuilder.getKieModule();

        // Создаём KieContainer
        KieContainer kieContainer = kieServices.newKieContainer(kieModule.getReleaseId());

        // Создаём KieSession
        KieSession session = kieContainer.newKieSession("defaultKieSession");
        if (session == null) {
            throw new RuntimeException("KieSession 'defaultKieSession' не найден!");
        }

        return session;
    }

    @Test
    void testHighRiskOCS() {
        KieSession kSession = getKieSession();
        Patient patient = new Patient();
        patient.setChestPain(true);
        patient.setEcgAbnormal(true);
        patient.setTroponinHigh(true); // Высокий риск
        kSession.insert(patient);
        int rulesFired = kSession.fireAllRules();
        kSession.dispose();

        assertEquals("Высокий риск ОКС", patient.getDiagnosis());
        assertTrue(rulesFired > 0);
    }

    @Test
    void testLowRiskOCS() {
        KieSession kSession = getKieSession();
        Patient patient = new Patient();
        patient.setChestPain(true);
        patient.setEcgAbnormal(false);
        patient.setTroponinHigh(false); // Низкий риск
        kSession.insert(patient);
        int rulesFired = kSession.fireAllRules();
        kSession.dispose();

        assertEquals("Низкий риск ОКС", patient.getDiagnosis());
        assertTrue(rulesFired > 0);
    }
}