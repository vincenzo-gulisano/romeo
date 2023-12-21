package com.vincenzogulisano.usecases.linearroad;

import java.io.BufferedReader;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.HashMap;
import java.util.function.Consumer;

import org.apache.commons.lang3.Validate;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentMonitor;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;

import common.metrics.Metric;
import common.metrics.Metrics;
import common.util.Util;
import component.source.SourceFunction;
import query.LiebreContext;

enum InjectorType {
    FIXEDRATE, REALRATE;
}

public class SourceReadFromFile implements SourceFunction<TupleInput>, EnvironmentMonitor {

    private static final Logger LOGGER = LogManager.getLogger();
    private static final long IDLE_SLEEP = 1000;
    private final String path;
    private BufferedReader reader;
    private volatile boolean done = false;
    private boolean enabled;
    private Metric injectionRateMetric;

    // private Random r;
    private InjectorType type;
    private long firstInvocationTs = -1;
    private long firstTupleTs = -1;
    private long lastSendNano = 0;
    private long nanoSleep;

    // private StatReporter statReporter;

    public SourceReadFromFile(String path, InjectorType type, long nanoSleep) {
        Validate.notBlank(path, "path");
        this.path = path;
        // throughputMetric =
        // LiebreContext.userMetrics().newCountPerSecondMetric("throughput", "rate");
        // r = new Random();
        this.type = type;
        this.nanoSleep = nanoSleep;
    }

    @Override
    public TupleInput get() {
        if (done) {
            LOGGER.debug("Finished processing input. Sleeping...");
            Util.sleep(IDLE_SLEEP);
            return null;
        }
        String t = readNextLine();
        TupleInput result = TupleInput.fromReading(t);

        if (result == null) {
            return null;
        }

        if (firstInvocationTs == -1) {
            firstInvocationTs = System.currentTimeMillis();
        }
        if (firstTupleTs == -1) {
            firstTupleTs = result.getTimestamp();
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
            LOGGER.warn("Text Source failed to read", e);
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
        try {
            this.reader = new BufferedReader(new FileReader(path));
        } catch (FileNotFoundException e) {
            throw new IllegalArgumentException(String.format("File not found: %s", path));
        }
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
            LOGGER.warn("Problem closing file {}: {}", path, e);
        }
        injectionRateMetric.disable();
    }

    @Override
    public boolean canRun() {
        return !done;
    }

    @Override
    public void setStatReporter(StatReporter reporter) {
        System.out.println("Setting stat reporter");
        // this.statReporter = reporter;

        // System.out.println("Registering consumers");
        // HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        // consumers.put("injectionrate", x -> reporter.report((long) x[0],
        // "injectionrate", ((Long) x[1]).doubleValue()));

        System.out.println("Creating statistics");
        injectionRateMetric = LiebreContext.userMetrics().newCountPerSecondMetric("injectionrate", "rate");

    }

}
