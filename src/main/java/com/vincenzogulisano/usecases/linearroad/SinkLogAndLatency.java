package com.vincenzogulisano.usecases.linearroad;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.function.Consumer;

import com.vincenzogulisano.javapythoncommunicator.EnvironmentMonitor;
import com.vincenzogulisano.javapythoncommunicator.StatReporter;

import common.metrics.Metric;
import common.metrics.TimeMetric;
import component.sink.BaseSink;
import component.sink.SinkFunction;
import query.LiebreContext;

public class SinkLogAndLatency extends BaseSink<TupleCarStops> implements EnvironmentMonitor {

    private Metric outrateMetric;
    private TimeMetric latencyMetric;
    private PrintWriter writer;
    private boolean writeOut;
    private String outPath;

    public SinkLogAndLatency(String id, SinkFunction<TupleCarStops> function, boolean writeOut, String outPath) {
        super(id, function);
        // outrateMetric = LiebreContext.userMetrics().newCountPerSecondMetric("outrate", "rate");
        // latencyMetric = LiebreContext.userMetrics().newAverageTimeMetric("latency", "average");
        this.writeOut = writeOut;
        this.outPath = outPath;
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
        super.processTuple(t);
        outrateMetric.record(1);
        latencyMetric.record(System.currentTimeMillis() - t.getStimulus());
        if (writeOut) {
            writer.println(t);
        }
    }

    @Override
    public void setStatReporter(StatReporter reporter) { System.out.println("Setting stat reporter");
        // this.statReporter = reporter;

        // System.out.println("Registering consumers");
        // HashMap<String, Consumer<Object[]>> consumers = new HashMap<>();
        // consumers.put("outrate", x -> reporter.report((long) x[0], "outrate", ((Long) x[1]).doubleValue()));
        // consumers.put("latency", x -> reporter.report((long) x[0], "latency", ((Long) x[1]).doubleValue()));

        System.out.println("Creating statistics");
        outrateMetric = LiebreContext.userMetrics().newCountPerSecondMetric("outrate", "rate");
        latencyMetric = LiebreContext.userMetrics().newAverageTimeMetric("latency", "average");

    }

}
