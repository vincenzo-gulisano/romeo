package com.vincenzogulisano.usecases.linearroad;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.TreeMap;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Consumer;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import com.vincenzogulisano.javapythoncommunicator.StatReporter;

import common.metrics.Metric;
import common.metrics.TimeMetric;
import component.sink.BaseSink;
import component.sink.SinkFunction;
import query.LiebreContext;

public class SinkLogAndLatency extends BaseSink<TupleCarStops> {

    private Metric outrateMetric;
    private TimeMetric latencyMetric;
    private PrintWriter writer;
    private boolean writeOut;
    private String outPath;

    public Logger logger = LogManager.getLogger();

    private volatile boolean resetRequest;
    private volatile boolean resetAck;
    private Lock resetLock;

    public SinkLogAndLatency(String id, SinkFunction<TupleCarStops> function, boolean writeOut, String outPath) {
        super(id, function);
        this.writeOut = writeOut;
        this.outPath = outPath;

        this.resetRequest = false;
        this.resetAck = false;
        this.resetLock = new ReentrantLock();

    }

    public void reset() {
        logger.debug("Registering reset request");
        resetAck = false;
        resetRequest = true;
        resetLock.lock();
        logger.debug("Got the reset lock");
        if (getInput().size() == 0) {
            logger.debug("No tuples in the input stream, resetting immediately");
            internalReset();
        } else {
            logger.debug("There exist tuples in the input stream, deferring the reset to main thread");
        }
        resetLock.unlock();
    }

    private void internalReset() {
        logger.debug("Clearing {} tuples in input stream", getInput().size());
        getInput().clear();
        outrateMetric.reset();
        latencyMetric.reset();
        logger.debug("Acking back to SPE");
        resetAck = true;
        resetRequest = false;
    }

    public boolean getResetAck() {
        return resetAck;
    }

    @Override
    public void enable() {
        super.enable();
        outrateMetric.enable();
        latencyMetric.enable();
        if (writeOut) {
            try {
                this.writer = new PrintWriter(new FileWriter(outPath), true);
            } catch (IOException e) {
                throw new IllegalArgumentException(String.format("Cannot write to file :%s", outPath));
            }
        }
    }

    @Override
    public void disable() {
        super.disable();
        outrateMetric.disable();
        latencyMetric.disable();
        if (writeOut) {
            writer.flush();
            writer.close();
        }
    }

    @Override
    public void processTuple(TupleCarStops t) {

        if (resetRequest) {
            logger.debug("Processing reset request");
            resetLock.lock();
            logger.debug("Got the reset lock");
            internalReset();
            resetLock.unlock();
        }

        super.processTuple(t);
        outrateMetric.record(1);
        latencyMetric.record(System.currentTimeMillis() - t.getStimulus());
        if (writeOut) {
            writer.println(t);
        }
    }

    public HashMap<String, Consumer<Object[]>> setStatReporter(StatReporter reporter) {
        logger.debug("Sink - Registering consumers");
        HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        consumers.put("outrate", x -> reporter.report((long) x[0], "outrate", ((Long) x[1]).doubleValue()));
        consumers.put("latency", x -> reporter.report((long) x[0], "latency", ((Long) x[1]).doubleValue()));

        return consumers;
    }

    public void createStatistics() {
        logger.debug("Sink - Creating statistics");
        outrateMetric = LiebreContext.userMetrics().newCountPerSecondMetric("outrate", "rate");
        latencyMetric = LiebreContext.userMetrics().newAverageTimeMetric("latency", "average");
    }

}
