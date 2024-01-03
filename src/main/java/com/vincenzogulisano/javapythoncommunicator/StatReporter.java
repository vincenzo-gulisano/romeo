package com.vincenzogulisano.javapythoncommunicator;

public interface StatReporter {

    void report(long ts, String id, double value);

    public void setResetRequest();

    public boolean getResetAcknowledged();

    public void setResetCompleted();

}
