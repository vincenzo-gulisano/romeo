package com.vincenzogulisano.woost;

import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map.Entry;

import common.metrics.Metric;
import common.metrics.TimeMetric;
import common.tuple.RichTuple;
import component.operator.in1.aggregate.BaseKeyExtractor;
import component.operator.in1.aggregate.TimeAggregate;
import query.LiebreContext;

@SuppressWarnings("unchecked")
public class WoostAggregate<IN extends RichTuple, OUT extends RichTuple> extends TimeAggregate<IN, OUT> {

    private WoostTimeWindow<IN, OUT> aggregateWindow;
    private HashMap<String, WoostTimeWindow<IN, OUT>> windows;
    private long earliestWinLeftBoundary = -1;

    private Metric windowsMetric;
    private Metric tuplesMetric;
    private Metric memoryMetric;

    // compression related
    private Metric compressionsMetric;
    private Metric decompressionMetric;
    private TimeMetric compressionRatio;

    private Metric maxEventTimeMetric;

    public WoostAggregate(
            String id,
            int instance,
            int parallelismDegree,
            long windowSize,
            long windowSlide,
            WoostTimeWindow<IN, OUT> aggregateWindow) {
        super(id, instance, parallelismDegree, windowSize, windowSlide, aggregateWindow, new BaseKeyExtractor<>());
        windows = new HashMap<>();
        this.aggregateWindow = aggregateWindow;
        windowsMetric = LiebreContext.userMetrics().newTotalCountMetric("windows", "count");
        tuplesMetric = LiebreContext.userMetrics().newTotalCountMetric("tuples", "count");
        memoryMetric = LiebreContext.userMetrics().newTotalCountMetric("memory", "size");

        // I am always creating the metrics, even if not used, so that each experiment
        // produces the same files
        compressionsMetric = LiebreContext.userMetrics().newTotalCountMetric("comp", "count");
        decompressionMetric = LiebreContext.userMetrics().newTotalCountMetric("dec", "count");
        compressionRatio = LiebreContext.userMetrics().newAverageTimeMetric("ratio", "percent");

        maxEventTimeMetric = LiebreContext.userMetrics().newTotalMaxMetric("eventtime", "max");

    }

    @Override
    public void enable() {
        super.enable();
        windowsMetric.enable();
        tuplesMetric.enable();
        memoryMetric.enable();
        compressionsMetric.enable();
        decompressionMetric.enable();
        maxEventTimeMetric.enable();
        compressionRatio.enable();
    }

    @Override
    public void disable() {
        super.disable();
        windowsMetric.disable();
        tuplesMetric.disable();
        memoryMetric.disable();
        compressionsMetric.disable();
        decompressionMetric.disable();
        maxEventTimeMetric.disable();
        compressionRatio.disable();
    }

    // Iterators, entries and wins
    Iterator<Entry<String, WoostTimeWindow<IN, OUT>>> i1;
    Entry<String, WoostTimeWindow<IN, OUT>> e1;
    WoostTimeWindow<IN, OUT> wToAdd;

    // Statistics
    long memoryChange;
    long tuplesChange;
    long windowsChange;

    public List<OUT> processTupleIn1(IN t) {
        
        // Prepare statistics vars
        memoryChange = 0;
        tuplesChange = 0;
        windowsChange = 0;

        List<OUT> result = new LinkedList<OUT>();

        checkIncreasingTimestamps(t);

        latestTimestamp = t.getTimestamp();

        long tL = getEarliestWinStartTS(latestTimestamp);

        while (earliestWinLeftBoundary != -1 && earliestWinLeftBoundary < tL && !windows.isEmpty()) {

            i1 = windows.entrySet().iterator();
            while (i1.hasNext()) {
                e1 = i1.next();

                e1.getValue().setLatestStimulus(t.getStimulus());
                OUT outT = e1.getValue().getAggregatedResult();
                if (outT != null) {
                    result.add(outT);
                }

                tuplesChange -= e1.getValue().getNumberOfTuples();
                memoryChange -= e1.getValue().getSizeInBytes();

                e1.getValue().slideTo(earliestWinLeftBoundary + WA);

                tuplesChange += e1.getValue().getNumberOfTuples();
                memoryChange += e1.getValue().getSizeInBytes();

                if (e1.getValue().isEmpty()) {
                    i1.remove();
                    windowsChange--;
                }
            }

            earliestWinLeftBoundary += WA;
        }

        String k = keyExtractor.getKey(t);

        if (!windows.containsKey(k)) {
            wToAdd = aggregateWindow.woostFactory();
            wToAdd.setKey(k);
            wToAdd.setInstanceNumber(instance);
            wToAdd.setParallelismDegree(parallelismDegree);
            wToAdd.slideTo(tL);
            windows.put(k, wToAdd);
            windowsChange++;
        }

        memoryChange -= windows.get(k).getSizeInBytes();

        windows.get(k).add(t);

        memoryChange += windows.get(k).getSizeInBytes();
        tuplesChange++;
        
        earliestWinLeftBoundary = tL;

        // Update metrics
        maxEventTimeMetric.record(t.getTimestamp());
        memoryMetric.record(memoryChange);
        tuplesMetric.record(tuplesChange);
        maxEventTimeMetric.record(t.getTimestamp());
        windowsMetric.record(windowsChange);
        compressionRatio.record(100);

        return result;
    }

}
