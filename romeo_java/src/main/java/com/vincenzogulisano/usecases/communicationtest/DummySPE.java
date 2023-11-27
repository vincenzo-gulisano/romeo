package com.vincenzogulisano.usecases.communicationtest;

import java.util.LinkedList;
import java.util.List;

import com.vincenzogulisano.javapythoncommunicator.Actionable;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;

public class DummySPE implements Actionable {

    private final List<DummyStatReporter> statReporters;

    public DummySPE(int numReporters, StatReporter statReporter) {
        this.statReporters = new LinkedList<>();
        for (int i = 0; i < numReporters; i++) {
            statReporters.add(new DummyStatReporter("reporter_" + i, statReporter));
        }
        startInternalThread();
    }

    private void startInternalThread() {
        Thread reportingThread = new Thread(() -> {
            while (true) {
                try {
                    Thread.sleep(1000);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                }
            }
        });

        // Set the thread as a daemon so it doesn't prevent the program from exiting
        reportingThread.setDaemon(true);

        // Start the thread
        reportingThread.start();
    }

    @Override
    public void actionA() {
        System.out.println("Unimplemented method 'actionA'");
    }

    @Override
    public void actionB() {
        System.out.println("Unimplemented method 'actionB'");
    }

    public static void main(String[] args) throws InterruptedException {

        DummySPE statReporter = new DummySPE(3, new StatReporter() {
            @Override
            public void report(long ts, String id, double value) {
                System.out.println("Custom Reporting - Timestamp: " + ts + ", ID: " + id + ", Value: " + value);
            }
        });

        Thread.sleep(10000);
    }
}
