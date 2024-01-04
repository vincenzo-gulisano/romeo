package com.vincenzogulisano.util;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class EpisodesLogger {

    private String fileName;
    private BufferedWriter writer;
    private int counter;

    public EpisodesLogger(String fileName) {
        this.fileName = fileName;
        this.counter = 0;

        try {
            this.writer = new BufferedWriter(new FileWriter(fileName));
            writer.write("ts,episode,event\n");

        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void writeStartEvent() {
        writeEvent("start");
    }

    public void writeEndEvent() {
        writeEvent("end");
        counter++;
    }

    private void writeEvent(String event) {
        String line = String.format("%d,%d,%s\n", System.currentTimeMillis()/1000, counter, event);

        try {
            writer.write(line);
            writer.flush();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void close() {
        try {
            if (writer != null) {
                writer.close();
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
