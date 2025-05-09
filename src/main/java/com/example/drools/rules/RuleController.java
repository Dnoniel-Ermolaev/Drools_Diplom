package com.example.drools;

import org.kie.api.KieServices;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class RuleController {

    private final KieContainer kieContainer;

    public RuleController() {
        KieServices kieServices = KieServices.Factory.get();
        this.kieContainer = kieServices.getKieClasspathContainer();

        // Отладка: выведем доступные KieBase и KieSession
        System.out.println("Доступные KieBase: " + kieContainer.getKieBaseNames());
        for (String kieBaseName : kieContainer.getKieBaseNames()) {
            System.out.println("KieSessions для " + kieBaseName + ": " + kieContainer.getKieSessionNamesInKieBase(kieBaseName));
        }

        // Проверяем, существует ли KieBase
        if (this.kieContainer.getKieBase("defaultKieBase") == null) {
            System.err.println("WARNING: Drools KieBase 'defaultKieBase' не найден. Проверьте kmodule.xml и расположение drl файла.");
        } else {
            System.out.println("Drools KieBase 'defaultKieBase' успешно загружен.");
        }
    }

    // Принимаем 5 параметров и возвращаем String
    @GetMapping("/run-rules")
    public String runDroolsRules(
            // Принимаем каждый параметр как String для удобства парсинга и проверки наличия
            @RequestParam(name = "chestPain", required = false) String chestPainStr,
            @RequestParam(name = "ecgAbnormal", required = false) String ecgAbnormalStr,
            @RequestParam(name = "troponinHigh", required = false) String troponinHighStr,
            @RequestParam(name = "heartRate", required = false) String heartRateStr,
            @RequestParam(name = "systolicBP", required = false) String systolicBPStr
    ) {
        // Создаём KieSession напрямую через имя сессии
        KieSession kieSession = kieContainer.newKieSession("defaultKieSession");
        if (kieSession == null) {
            return "Ошибка: Drools KieSession 'defaultKieSession' не найден.";
        }

        Patient patient = new Patient(); // Создаем новый объект пациента

        // Устанавливаем поля пациента, парся значения из строк.
        // Сеттеры в классе Patient устанавливают соответствующие флаги ...Set только если сеттер вызван.
        if (chestPainStr != null) {
            try { patient.setChestPain(Boolean.parseBoolean(chestPainStr)); } catch (IllegalArgumentException e) { System.err.println("Неверный формат chestPain: " + chestPainStr); }
        }
        if (ecgAbnormalStr != null) {
            try { patient.setEcgAbnormal(Boolean.parseBoolean(ecgAbnormalStr)); } catch (IllegalArgumentException e) { System.err.println("Неверный формат ecgAbnormal: " + ecgAbnormalStr); }
        }
        if (troponinHighStr != null) {
            try { patient.setTroponinHigh(Boolean.parseBoolean(troponinHighStr)); } catch (IllegalArgumentException e) { System.err.println("Неверный формат troponinHigh: " + troponinHighStr); }
        }
        // Числовые поля парсим в double
        if (heartRateStr != null && !heartRateStr.trim().isEmpty()) { // Проверяем на null и пустую строку (с учетом пробелов)
            try {
                double parsedHR = Double.parseDouble(heartRateStr);
                if (parsedHR != 0.0) { // Проверяем, что значение не 0.0
                    patient.setHeartRate(parsedHR); // Сеттер установит heartRateSet = true
                } else {
                    System.out.println("Info: Received heartRate = 0.0. Treating as unset.");
                    // Если 0.0, не вызываем сеттер, heartRate останется 0.0, heartRateSet останется false.
                }
            } catch (NumberFormatException e) {
                System.err.println("Неверный формат для heartRate: '" + heartRateStr + "'. Treating as unset.");
                // Парсинг не удался, heartRate останется 0.0, heartRateSet останется false.
            }
        }

        if (systolicBPStr != null && !systolicBPStr.trim().isEmpty()) { // Проверяем на null и пустую строку (с учетом пробелов)
            try {
                double parsedBP = Double.parseDouble(systolicBPStr);
                if (parsedBP != 0.0) { // Проверяем, что значение не 0.0
                    patient.setSystolicBP(parsedBP); // Сеттер установит systolicBPSet = true
                } else {
                    System.out.println("Info: Received systolicBP = 0.0. Treating as unset.");
                    // Если 0.0, не вызываем сеттер, systolicBP останется 0.0, systolicBPSet останется false.
                }
            } catch (NumberFormatException e) {
                System.err.println("Неверный формат для systolicBP: '" + systolicBPStr + "'. Treating as unset.");
                // Парсинг не удался, systolicBP останется 0.0, systolicBPSet останется false.
            }
        }

        System.out.println("Вставлен пациент (исходные данные): " + patient); // Логирование

        kieSession.insert(patient); // Вставляем факт

        int rulesFired = kieSession.fireAllRules(); // Запускаем правила
        System.out.println("Сработало правил: " + rulesFired);

        String finalDiagnosis = patient.getDiagnosis(); // Получаем результат

        kieSession.dispose(); // Освобождаем ресурсы

        System.out.println("Финальный диагноз от Drools: " + finalDiagnosis); // Логирование

        // Возвращаем диагноз или сообщение по умолчанию
        return finalDiagnosis != null ? finalDiagnosis : "Диагноз не установлен (null)";
    }
}