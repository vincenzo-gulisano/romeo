package com.vincenzogulisano.javapythoncommunicator;

import com.vincenzogulisano.util.EpisodesLogger;

public interface StatReporter {

    void report(long ts, String id, double value);

    public void setResetRequest();

    public boolean getResetAcknowledged();

    public void setResetCompleted();

    public void registerLogger(EpisodesLogger logger);

}
