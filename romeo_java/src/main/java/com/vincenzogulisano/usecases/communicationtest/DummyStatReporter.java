package com.vincenzogulisano.usecases.communicationtest;

import java.util.Random;

import com.vincenzogulisano.javapythoncommunicator.StatReporter;

public class DummyStatReporter {

    private final String id;
    private final StatReporter statReporter;
    private final Random r;

    public DummyStatReporter(String id, StatReporter statReporter) {
        this.id = id;
        this.statReporter = statReporter;
        r = new Random();
        startReportingThread();
    }

    private void startReportingThread() {
        Thread reportingThread = new Thread(() -> {
            while (true) {
                try {
                    // Sleep for one second
                    Thread.sleep(1000);
                    // Invoke report with current time, id, and a random double
                    statReporter.report(System.currentTimeMillis(), id, r.nextDouble());
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

    public static void main(String[] args) throws InterruptedException {
        // Example usage:
        // Create an instance of StatReporterImpl
        DummyStatReporter statReporter = new DummyStatReporter("exampleId", new StatReporter() {
            @Override
            public void report(long ts, String id, double value) {
                System.out.println("Custom Reporting - Timestamp: " + ts + ", ID: " + id + ", Value: " + value);
            }
        });

        Thread.sleep(10000);
    }
}
