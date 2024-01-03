package com.vincenzogulisano.usecases.linearroad;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.function.Consumer;

import org.apache.commons.lang3.Validate;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;
import common.metrics.Metric;
import common.util.Util;
import component.source.SourceFunction;
import query.LiebreContext;

enum InjectorType {
    FIXEDRATE, REALRATE, RL;
}

public class SourceReadFromFile implements SourceFunction<TupleInput> {

    private final long IDLE_SLEEP;
    private final String path;
    private BufferedReader reader;
    private volatile boolean done;
    private boolean enabled;
    private Metric injectionRateMetric;

    private InjectorType type;
    private long firstInvocationTs;
    private long firstTupleTs;
    private long lastSendNano;
    private long nanoSleep;

    private long startingTS;
    private long WS;
    private long sleepBeforeRealRate;
    private boolean firstTupleAtRealRate;
    private boolean firstTuplesSkipped;

    private volatile boolean resetRequest;
    private volatile boolean resetAck;
    private volatile boolean resetReader;
    private volatile boolean waitingForSPEGreenlightToStartSendingStateFillingTuples;
    private volatile boolean ackFromSPEGreenlightToStartSendingStateFillingTuples;
    private volatile boolean allStateFillingTuplesSent;
    private volatile boolean waitingForSPEGreenlightToStartSendingRealRateTuples;
    private volatile boolean ackFromSPEGreenlightToStartSendingRealRateTuples;

    public SourceReadFromFile(String path, InjectorType type, long nanoSleep, long startingTS, long WS) {
        Validate.notBlank(path, "path");
        this.path = path;
        this.type = type;
        this.nanoSleep = nanoSleep;
        this.startingTS = startingTS;
        this.WS = WS;
        IDLE_SLEEP = 1000;
        done = false;
        firstInvocationTs = -1;
        firstTupleTs = -1;
        lastSendNano = 0;
        sleepBeforeRealRate = 5000;
        firstTupleAtRealRate = true;
        firstTuplesSkipped = false;
        resetRequest = false;
        resetAck = false;
        resetReader = false;
        waitingForSPEGreenlightToStartSendingStateFillingTuples = false;
        ackFromSPEGreenlightToStartSendingStateFillingTuples = false;
        allStateFillingTuplesSent = false;
        waitingForSPEGreenlightToStartSendingRealRateTuples = false;
        ackFromSPEGreenlightToStartSendingRealRateTuples = false;
    }

    public void setStartingTS(long startingTS) {
        this.startingTS = startingTS;
    }

    public SourceReadFromFile(String path, InjectorType type, long nanoSleep) {
        this(path, type, nanoSleep, 0, 0);
    }

    private void initializeReader() {
        try {
            this.reader = new BufferedReader(new FileReader(path));
        } catch (FileNotFoundException e) {
            throw new IllegalArgumentException(String.format("File not found: %s", path));
        }
        firstInvocationTs = -1;
        firstTupleTs = -1;
        lastSendNano = 0;
        firstTupleAtRealRate = true;
        firstTuplesSkipped = false;
    }

    @Override
    public TupleInput get() {

        if (done) {
            System.out.println("Finished processing input. Sleeping...");
            Util.sleep(IDLE_SLEEP);
            return null;
        }

        if (resetRequest) {
            resetRequest = false; // Clear the request
            resetAck = true; // Tell SPE I have stopped
            resetReader = true; // Make sure next call I reset the reader
            waitingForSPEGreenlightToStartSendingStateFillingTuples = true; // Wait for ack from SPE to start sending
                                                                            // state filling tuples
            ackFromSPEGreenlightToStartSendingStateFillingTuples = false; // Register the ack has not been received yet
            allStateFillingTuplesSent = false; // Register we still have to complete this, since the SPE needs to know
            waitingForSPEGreenlightToStartSendingRealRateTuples = true; // Wait for ack from SPE to start sending
                                                                        // real rate tuples
            ackFromSPEGreenlightToStartSendingRealRateTuples = false; // Register the ack has not been received yet
            return null;
        }

        // If the reader has not been created yet or if a reset was requested and, thus,
        // the reader should be recreated, create a new reader
        if (reader == null || resetReader) {
            initializeReader();
            if (resetReader) {
                System.out.println("Source - re-initialized reader because of a reset");
                resetReader = false;
            }
        }

        String t = readNextLine();
        if (t == null) {
            return null;
        }
        TupleInput result = TupleInput.fromReading(t);

        if (firstInvocationTs == -1) {
            firstInvocationTs = System.currentTimeMillis();
        }
        if (firstTupleTs == -1) {
            firstTupleTs = result.getTimestamp();
        }

        if (!firstTuplesSkipped && type == InjectorType.RL) {
            System.out.println(
                    "This is a RL injector, skipping all tuples with timestamp lower than " + (startingTS - WS));
            while (result.getTimestamp() - firstTupleTs < startingTS - WS) {
                t = readNextLine();
                if (t == null) {
                    return null;
                }
                result = TupleInput.fromReading(t);
            }
            firstTuplesSkipped = true;
        }

        if (waitingForSPEGreenlightToStartSendingStateFillingTuples) {
            System.out.println("Source - checking if we got greenlight from SPE to send state filling tuples");
            while (!ackFromSPEGreenlightToStartSendingStateFillingTuples) {
                Util.sleep(50);
            }
            System.out.println("Source - got greenlight from SPE to send state filling tuples");
            waitingForSPEGreenlightToStartSendingStateFillingTuples = false;
        }

        switch (type) {
            case FIXEDRATE:
                while (System.nanoTime() - lastSendNano < nanoSleep) {
                }
                lastSendNano = System.nanoTime();
                break;
            case REALRATE:
                while ((System.currentTimeMillis() - firstInvocationTs) < (result.getTimestamp() - firstTupleTs)
                        * 1000) {
                    try {
                        Thread.sleep(1);
                    } catch (InterruptedException e) {
                        e.printStackTrace();
                    }
                }
                break;
            case RL:
                // Start the real sleep only if the first WS is over
                if (result.getTimestamp() - firstTupleTs >= startingTS) {
                    // The very first time, actually sleep for a while and then reset
                    // firstInvocationTs and firstTupleTs
                    if (firstTupleAtRealRate) {

                        allStateFillingTuplesSent = true;

                        if (waitingForSPEGreenlightToStartSendingRealRateTuples) {
                            System.out.println(
                                    "Source - ready to send real tuples, but waiting for the ack from the SPE");
                            while (!ackFromSPEGreenlightToStartSendingRealRateTuples) {
                                Util.sleep(50);
                            }
                            System.out.println(
                                    "Source - ack received");
                            waitingForSPEGreenlightToStartSendingRealRateTuples = false;
                        }
                        System.out.println("Sleeping " + sleepBeforeRealRate + " ms before starting for real");
                        firstTupleAtRealRate = false;
                        try {
                            Thread.sleep(sleepBeforeRealRate);
                        } catch (InterruptedException e) {
                            System.out.println("Thread sleep Interrupted Exception");
                        }
                        firstInvocationTs = System.currentTimeMillis();
                    }
                    while ((System.currentTimeMillis()
                            - firstInvocationTs) < (result.getTimestamp() - (firstTupleTs + startingTS))
                                    * 1000) {
                        try {
                            Thread.sleep(1);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
                break;
            default:
                break;
        }
        injectionRateMetric.record(1);

        result.setStimulus(System.currentTimeMillis());
        return result;
    }

    private String readNextLine() {
        String nextLine = null;
        try {
            nextLine = reader.readLine();
        } catch (IOException e) {
            System.out.println("Text Source failed to read " + e);
        }
        done = (nextLine == null);
        return nextLine;
    }

    @Override
    public boolean isInputFinished() {
        return done;
    }

    @Override
    public void enable() {
        this.enabled = true;
        injectionRateMetric.enable();
    }

    @Override
    public boolean isEnabled() {
        return enabled;
    }

    @Override
    public void disable() {
        this.enabled = false;
        try {
            this.reader.close();
        } catch (IOException e) {
            System.out.println(String.format("Problem closing file %s: %s", path, e));
        }
        injectionRateMetric.disable();
    }

    @Override
    public boolean canRun() {
        return !done;
    }

    public HashMap<String, Consumer<Object[]>> setStatReporter(StatReporter reporter) {
        System.out.println("Source - Registering consumers");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        consumers.put("injectionrate", x -> reporter.report((long) x[0], "injectionrate", ((Long) x[1]).doubleValue()));

        return consumers;
    }

    public void createStatistics() {
        System.out.println("Source - Creating statistics");
        injectionRateMetric = LiebreContext.userMetrics().newCountPerSecondMetric("injectionrate", "rate");
    }

    public void registerResetRequest() {
        resetAck = false;
        resetRequest = true;
    }

    public boolean getResetAck() {
        return resetAck;
    }

    public void giveGreenlightToStartSendingStateFillingTuples() {
        ackFromSPEGreenlightToStartSendingStateFillingTuples = true;
    }

    public void giveGreenlightToStartSendingRealRateTuples() {
        ackFromSPEGreenlightToStartSendingRealRateTuples = true;
    }

    public boolean areAllStateFillingTuplesSent() {
        return allStateFillingTuplesSent;
    }

    // public void reset() {
    // // resetRequest = false;
    // // resetAck = false;
    // // reset = true;
    // }
}
