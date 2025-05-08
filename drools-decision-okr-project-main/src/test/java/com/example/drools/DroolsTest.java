package com.example.drools;

import static org.junit.jupiter.api.Assertions.*;
import org.junit.jupiter.api.Test;
import org.kie.api.KieServices;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;

class DroolsTest {

    private KieSession getKieSession() {
        KieServices kieServices = KieServices.Factory.get();
        KieContainer kieContainer = kieServices.getKieClasspathContainer();
        return kieContainer.newKieSession();
    }

    @Test
    void testHighRiskOCS() {
        KieSession kSession = getKieSession();
        Patient patient = new Patient();
        patient.setChestPain(true);
        patient.setEcgAbnormal(true);
        patient.setTroponinHigh(true); // High risk
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
        patient.setTroponinHigh(false); // Low risk
        kSession.insert(patient);
        int rulesFired = kSession.fireAllRules();
        kSession.dispose();

        assertEquals("Низкий риск ОКС", patient.getDiagnosis());
        assertTrue(rulesFired > 0);
    }
} // Ensure this is the only closing brace for the class