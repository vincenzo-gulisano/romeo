package com.vincenzogulisano.usecases.communicationtest;

import java.util.LinkedList;
import java.util.List;

import com.vincenzogulisano.javapythoncommunicator.Actionable;
import com.vincenzogulisano.javapythoncommunicator.EnvironmentMonitor;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;

public class DummySPE implements Actionable, EnvironmentMonitor {

    private final int numReporters;
    private final List<DummyStatReporter> statReporters;

    public DummySPE(int numReporters) {
        this.numReporters = numReporters;
        this.statReporters = new LinkedList<>();
    }

    @Override
    public void setStatReporter(StatReporter reporter) {
        for (int i = 0; i < numReporters; i++) {
            statReporters.add(new DummyStatReporter("reporter_" + i, reporter));
        }
        startInternalThread();
    }

    private void startInternalThread() {
        Thread reportingThread = new Thread(() -> {
            while (true) {
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    // e.printStackTrace();
                }
            }
        });

        // Set the thread as a daemon so it doesn't prevent the program from exiting
        reportingThread.setDaemon(true);

        // Start the thread
        reportingThread.start();
    }

    @Override
    public void changeD(long v) {
        System.out.println("Changing D to " + v);
    }

}
