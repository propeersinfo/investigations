import org.junit.Test;

import java.util.ArrayList;
import java.util.List;

public class DistributionRandomizerTest {
    @Test
    public void smoke() {
        List<RandomizerByDistribution.Share<String>> ref = create_ref_distribution();
        RandomizerByDistribution<String> rnd = new RandomizerByDistribution<String>(ref);
        Distribution<String> actualDistribution = new Distribution<String>();
        for(int i = 0; i < 50*1000; i++) {
            String next = rnd.next();
            actualDistribution.increment(next);
        }
        actualDistribution.debug();
    }

    private static List<RandomizerByDistribution.Share<String>> create_ref_distribution() {
        List<RandomizerByDistribution.Share<String>> ref = new ArrayList<RandomizerByDistribution.Share<String>>();

        float[] shares = { 0.1F, 0.3F, 0.4F, 0.2F };
        for(float share : shares) {
            ref.add(new RandomizerByDistribution.Share<String>("Obj"+share, share));
        }
        return ref;
    }
}
