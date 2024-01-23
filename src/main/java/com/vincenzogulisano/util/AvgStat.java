package com.vincenzogulisano.util;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

public class AvgStat {

    private final PrintWriter out;
    private long sum;
    private long count;
    private long prevSec;

    public AvgStat(String outputFile, boolean autoFlush) {
        this.sum = 0;
        this.count = 0;

        FileWriter outFile;
        try {
            outFile = new FileWriter(outputFile);
            out = new PrintWriter(outFile, autoFlush);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        prevSec = System.currentTimeMillis() / 1000;

    }

    public long add(long v, long thisSec) {

        long highestLat = -1;

        while (prevSec < thisSec) {
            out.println(prevSec + "," + (count != 0 ? sum / count : -1));
            highestLat = (count != 0 && sum / count > highestLat) ? sum / count : highestLat;
            sum = 0;
            count = 0;
            prevSec++;
        }

        sum += v;
        count++;

        return highestLat;

    }

    // public long add(long v) {
    //     return add(v, System.currentTimeMillis() / 1000);
    // }

    public void flush() {
        out.flush();
    }

    public void close() {
        // long thisSec = System.currentTimeMillis() / 1000;
        // while (prevSec <= thisSec) {
        //     out.println(prevSec + "," + (count != 0 ? sum / count : -1));
        //     count = 0;
        //     prevSec++;
        // }
        out.flush();
        out.close();
    }

}