import com.webfuzzing.commons.faults.DefinedFaultCategory;

public class Codes {
    public static void main(String[] a) {
        for (DefinedFaultCategory c : DefinedFaultCategory.values()) {
            System.out.println(c.getCode() + "\t" + c.name() + "\t" + c.getDescriptiveName());
        }
    }
}
