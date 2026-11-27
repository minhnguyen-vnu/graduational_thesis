import java.util.*;
import java.util.jar.*;

public class Classes {

    static String iface(Class<?> c) {
        List<String> out = new ArrayList<>();
        for (Class<?> i : c.getInterfaces()) {
            if (i.getName().startsWith("org.evomaster")) out.add(i.getSimpleName());
        }
        return out.isEmpty() ? "" : " implements " + String.join(", ", out);
    }

    static void chain(String name) throws Exception {
        Class<?> c = Class.forName(name);
        List<String> parts = new ArrayList<>();
        while (c != null && c != Object.class) {
            parts.add(c.getSimpleName() + (java.lang.reflect.Modifier.isAbstract(c.getModifiers()) ? "(abstract)" : "") + iface(c));
            c = c.getSuperclass();
        }
        System.out.println(String.join("  ->  ", parts));
    }

    public static void main(String[] args) throws Exception {
        String[] names = {
            "org.evomaster.core.problem.rest.data.RestIndividual",
            "org.evomaster.core.problem.rest.resource.RestResourceCalls",
            "org.evomaster.core.problem.enterprise.EnterpriseActionGroup",
            "org.evomaster.core.problem.rest.data.RestCallAction",
            "org.evomaster.core.problem.rest.param.BodyParam",
            "org.evomaster.core.problem.rest.param.PathParam",
            "org.evomaster.core.problem.rest.param.QueryParam",
            "org.evomaster.core.problem.rest.param.HeaderParam",
            "org.evomaster.core.problem.rest.param.FormParam",
            "org.evomaster.core.search.gene.ObjectGene",
            "org.evomaster.core.search.gene.string.StringGene",
            "org.evomaster.core.search.gene.collection.EnumGene",
            "org.evomaster.core.search.gene.BooleanGene",
            "org.evomaster.core.search.gene.numeric.IntegerGene",
            "org.evomaster.core.search.gene.collection.ArrayGene",
            "org.evomaster.core.search.gene.collection.TaintedArrayGene",
            "org.evomaster.core.search.gene.placeholder.CycleObjectGene",
            "org.evomaster.core.search.gene.placeholder.LimitObjectGene",
            "org.evomaster.core.search.gene.wrapper.OptionalGene",
            "org.evomaster.core.search.gene.wrapper.NullableGene",
            "org.evomaster.core.search.gene.wrapper.CustomMutationRateGene",
            "org.evomaster.core.search.gene.wrapper.ChoiceGene",
            "org.evomaster.core.search.gene.wrapper.FlexibleGene",
            "org.evomaster.core.problem.rest.data.RestCallResult",
            "org.evomaster.core.problem.httpws.auth.HttpWsAuthenticationInfo",
            "org.evomaster.core.problem.httpws.auth.HttpWsNoAuth",
            "org.evomaster.core.search.EvaluatedIndividual",
            "org.evomaster.core.search.FitnessValue"
        };
        System.out.println("=== chuoi lop cha");
        for (String n : names) chain(n);

        System.out.println("=== moi lop gene implements WrapperGene trong jar");
        Class<?> wrapper = Class.forName("org.evomaster.core.search.gene.interfaces.WrapperGene");
        Class<?> gene = Class.forName("org.evomaster.core.search.gene.Gene");
        List<String> wrappers = new ArrayList<>();
        int genes = 0;
        try (JarFile jar = new JarFile(args[0])) {
            for (Enumeration<JarEntry> en = jar.entries(); en.hasMoreElements(); ) {
                String e = en.nextElement().getName();
                if (!e.startsWith("org/evomaster/core/search/gene/") || !e.endsWith(".class") || e.contains("$")) continue;
                Class<?> c;
                try { c = Class.forName(e.replace('/', '.').replace(".class", ""), false, Classes.class.getClassLoader()); } catch (Throwable t) { continue; }
                if (gene.isAssignableFrom(c) && !java.lang.reflect.Modifier.isAbstract(c.getModifiers())) genes++;
                if (wrapper.isAssignableFrom(c) && c != wrapper) wrappers.add(c.getName().replace("org.evomaster.core.search.gene.", "") + " extends " + c.getSuperclass().getSimpleName());
            }
        }
        Collections.sort(wrappers);
        for (String w : wrappers) System.out.println(w);
        System.out.println("so lop gene cu the (khong abstract) trong jar: " + genes);
    }
}
