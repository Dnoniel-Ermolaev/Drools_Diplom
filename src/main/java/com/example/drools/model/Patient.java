package com.example.drools;

public class Patient {
    private boolean chestPain;      // Боль в груди
    private boolean chestPainSet = false;

    private boolean ecgAbnormal;    // Отклонения на ЭКГ
    private boolean ecgAbnormalSet = false;

    private boolean troponinHigh;   // Уровень тропонина повышен
    private boolean troponinHighSet = false;

    private double  heartRate;          // Частота сердечных сокращений (ЧСС)
    private boolean heartRateSet = false;

    private double  systolicBP;         // Систолическое АД
    private boolean systolicBPSet = false;

    private String diagnosis;     // Результирующий диагноз

    public Patient() {
    }

    // Геттеры для доступа к данным

    public boolean isChestPain() { return chestPain; }
    public boolean isChestPainSet() { return chestPainSet; }

    public boolean isEcgAbnormal() { return ecgAbnormal; }
    public boolean isEcgAbnormalSet() { return ecgAbnormalSet; }

    public boolean isTroponinHigh() { return troponinHigh; }
    public boolean isTroponinHighSet() { return troponinHighSet; }

    public double getHeartRate() { return heartRate; }
    public boolean isHeartRateSet() { return heartRateSet; }

    public double getSystolicBP() { return systolicBP; }
    public boolean isSystolicBPSet() { return systolicBPSet; }


    // Геттер для поля результата
    public String getDiagnosis() { return diagnosis; }


    // Сеттеры для установки входных данных
    // Каждый сеттер данных также устанавливает соответствующий флаг "Set" в true.

    public void setChestPain(boolean chestPain) {
        this.chestPain = chestPain;
        this.chestPainSet = true;
    }

    public void setEcgAbnormal(boolean ecgAbnormal) {
        this.ecgAbnormal = ecgAbnormal;
        this.ecgAbnormalSet = true;
    }

    public void setTroponinHigh(boolean troponinHigh) {
        this.troponinHigh = troponinHigh;
        this.troponinHighSet = true;
    }

    public void setHeartRate(double heartRate) {
        this.heartRate = heartRate;
        this.heartRateSet = true;
    }

    public void setSystolicBP(double systolicBP) {
        this.systolicBP = systolicBP;
        this.systolicBPSet = true;
    }

    public void setDiagnosis(String diagnosis) {
        this.diagnosis = diagnosis;
    }

}
