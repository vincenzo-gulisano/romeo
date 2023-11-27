package com.vincenzogulisano.javapythoncommunicator;

import com.vincenzogulisano.usecases.communicationtest.DummySPE;

public class JPComm implements StatReporter {

    private final Actionable actionable;

    private JPComm(Actionable actionable) {
        this.actionable = actionable;
    }

    public static JPComm createInstance(Actionable actionable) {
        JPComm jpc = new JPComm(actionable);
        actionable.setStatReporter(jpc);
        jpc.startInternalThread();
        return jpc;
    }

    private void startInternalThread() {
        Thread reportingThread = new Thread(() -> {
            while (true) {
                try {

                    // Temp implementation

                    Thread.sleep(1000);

                    actionable.actionA();

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
    public void report(long ts, String id, double value) {
        System.out.println("Received report for ts:" + ts + " id:" + id + " value:" + value);
    }


    public static void main(String[] args) throws InterruptedException {

        DummySPE dummySPE = new DummySPE(3);
        JPComm jpc = JPComm.createInstance(dummySPE);

        Thread.sleep(10000);
    }

}
