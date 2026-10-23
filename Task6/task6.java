import java.util.concurrent.atomic.AtomicInteger;

public class Task6 {
    static int counter = 0;
    static AtomicInteger counter_a = new AtomicInteger(0);

    public static void main(String[] args) throws Exception {
        Runnable task = () -> {
            for (int i = 0; i < 2_000_000; i++) counter++;
        };
        Runnable task_atomic = () -> {
            for (int i = 0; i < 2_000_000; i++) counter_a.incrementAndGet();
        };
        Thread t1 = new Thread(task);
        Thread t2 = new Thread(task);
        Thread t3 = new Thread(task);
        Thread t4 = new Thread(task);


        t1.start(); t2.start(); t3.start(); t4.start();

        t1.join(); t2.join(); t3.join(); t4.join();
        int expected = 8_000_000;
        int actual = counter;
        double lostPercent = (double) (expected - actual) / expected * 100;

        System.out.println("Expected final value: " + expected);
        System.out.println("Actual final value:   " + actual);
        System.out.printf("Lost updates: %.2f%%%n", lostPercent);

        Thread t1_a = new Thread(task);
        Thread t2_a = new Thread(task);
        Thread t3_a = new Thread(task);
        Thread t4_a = new Thread(task);

        t1_a.start(); t2_a.start(); t3_a.start(); t4_a.start();
        t1_a.join();  t2_a.join();  t3_a.join();  t4_a.join();

=        int expected_a = 8_000_000;
        int actual_a = counter_a.get();
        double lostPercent_a = (double) (expected_a - actual_a) / expected_a * 100;

        System.out.println("Expected final value: " + expected_a);
        System.out.println("Actual final value:   " + actual_a);
        System.out.printf("Lost updates: %.2f%%%n", lostPercent_a);
    }
}