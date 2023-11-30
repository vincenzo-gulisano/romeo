package com.vincenzogulisano.util;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import org.xerial.snappy.Snappy;

import com.vincenzogulisano.usecases.linearroad.TupleInput;
import com.vincenzogulisano.usecases.linearroad.WindowCountStops;

import java.io.Serializable;

class MyObject implements Serializable {
    private static final long serialVersionUID = 1L;

    private String name;
    private int age;

    public MyObject() {
    }

    public MyObject(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

    @Override
    public String toString() {
        return "MyObject [name=" + name + ", age=" + age + "]";
    }
}

public class SnappyExample {
    public static void main(String[] args) throws IOException, ClassNotFoundException {

        WindowCountStops w = new WindowCountStops();
        w.setInstanceNumber(0);
        w.setKey("ABCD");
        w.setLatestStimulus(0);
        w.setParallelismDegree(0);
        w.slideTo(0);
        for (int i = 0; i < 100; i++) {
            w.add(TupleInput.fromReading("0,86400,0,10,0,0,1,37,200639"));
        }
        System.out.println("w length: " + w.getSizeInBytes());

        // Serialize object to byte array
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ObjectOutputStream oos = new ObjectOutputStream(baos);

        byte[] data = null;
        byte[] compressed = null;
        long before = System.currentTimeMillis();
        for (int i = 0; i < 10000; i++) {
            baos = new ByteArrayOutputStream();
            oos = new ObjectOutputStream(baos);
            oos.writeObject(w);
            oos.close();
            data = baos.toByteArray();
            compressed = Snappy.compress(data);
        }
        System.out.println("Average compression time: "+(System.currentTimeMillis()-before)/10000.0);

        System.out.println("data length: " + data.length);
        // Compress byte array
        System.out.println("compressed length: " + compressed.length);

        byte[] restored = null;
        WindowCountStops restoredObj = null;
        before = System.currentTimeMillis();
        for (int i = 0; i < 10000; i++) {
            restored = Snappy.uncompress(compressed);
            restoredObj = (WindowCountStops) new ObjectInputStream(new ByteArrayInputStream(restored))
                .readObject();
        }
        System.out.println("Average decompression time: "+(System.currentTimeMillis()-before)/10000.0);

        // Decompress byte array
        System.out.println("restored length: " + restored.length);

        System.out.println("Original object: " + w);
        System.out.println("Restored object: " + restoredObj);
    }
}
