package com.vincenzogulisano.javapythoncommunicator;

import java.io.IOException;
import java.time.Duration;
import java.util.Collections;
import java.util.Properties;

import org.apache.commons.cli.ParseException;
import org.apache.kafka.clients.consumer.Consumer;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.Producer;
import org.apache.kafka.common.serialization.StringDeserializer;

import com.vincenzogulisano.usecases.linearroad.QueryCountConsecutiveStops;

public class JPComm {

    private Actionable actionable;
    private Properties properties;
    private Producer<String, String> producer;
    private Consumer<String, String> consumer;
    private EnvironmentStateCalculator esc;

    private JPComm(Actionable actionable) {
        this.actionable = actionable;

        properties = new Properties();
        // TODO this should not be hardcoded!
        properties.put("bootstrap.servers", "michelangelo.cse.chalmers.se:9092");
        // TODO this should not be hardcoded!
        properties.put("group.id", "0");
        properties.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        properties.put("key.deserializer", StringDeserializer.class.getName());
        properties.put("value.deserializer", StringDeserializer.class.getName());

        producer = new KafkaProducer<>(properties);
        consumer = new KafkaConsumer<>(properties);
        // TODO topic should not be hardcoded!
        consumer.subscribe(Collections.singletonList("dchanges"));
        esc = new EnvironmentStateCalculator(20, producer);

    }

    public static JPComm createInstance(Actionable actionable, EnvironmentMonitor monitor) {
        JPComm jpc = new JPComm(actionable);
        monitor.setStatReporter(jpc.esc);
        return jpc;
    }

    public void startInternalThread() {
        try {

            Thread reportingThread = new Thread(() -> {

                while (true) {
                    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(1000));
                    // System.out.println("Checking consumer records...");
                    records.forEach(record -> {
                        System.out.println("... got " + record);
                        // Parse and process the received message
                        String[] parts = record.value().split(",");
                        if (parts[0].equals("changeD")) {
                            String action = parts[1];
                            Long change = Long.parseLong(action);
                            actionable.changeD(change);
                        } else if (parts[0].equals("reset")) {
                            actionable.reset();
                        } else {
                            throw new RuntimeException("Unknown command " + record.value());
                        }
                    });
                }
            });

            // Set the thread as a daemon so it doesn't prevent the program from exiting
            reportingThread.setDaemon(true);

            // Start the thread
            reportingThread.start();

        } catch (Exception e) {
            System.out.println(e);
        }

    }

    // @Override
    // public void report(long ts, String id, double value) {
    //     // System.out.println("Received report for ts:" + ts + " id:" + id + " value:" +
    //     // value);
    //     // Create a message and send it to the 'stats' topic
    //     // TODO topic should not be hardcoded!
    //     producer.send(new ProducerRecord<>("stats", String.format("%d,%s,%.2f", ts, id, value)));
    // }

    public static void main(String[] args) throws InterruptedException, ParseException, IOException {

        QueryCountConsecutiveStops q = new QueryCountConsecutiveStops();
        q.createQuery(args);
        JPComm jpc = JPComm.createInstance(q, q);

        jpc.startInternalThread();

        q.activateQuery();
        // Util.sleep(q.getQueryDuration());
        // q.deactivateQuery();
    }

}
