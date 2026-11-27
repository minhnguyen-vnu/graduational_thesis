import org.evomaster.core.EMConfig;
import org.evomaster.core.problem.rest.schema.*;
import org.evomaster.core.problem.rest.builder.RestActionBuilderV3;
import org.evomaster.core.problem.rest.data.*;
import org.evomaster.core.problem.rest.param.*;
import org.evomaster.core.problem.api.param.Param;
import org.evomaster.core.problem.rest.service.RestSecurityBuilder;
import org.evomaster.core.search.StructuralElement;
import org.evomaster.core.search.action.*;
import org.evomaster.core.search.gene.*;
import org.evomaster.core.search.gene.wrapper.*;
import org.evomaster.core.search.gene.collection.*;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.service.Randomness;
import java.lang.reflect.Method;
import java.nio.file.*;
import java.util.*;

public class Tree {

    static String info(StructuralElement e) {
        StringBuilder sb = new StringBuilder(e.getClass().getSimpleName());
        if (e instanceof Param) sb.append(" name=").append(((Param) e).getName());
        if (e instanceof Gene) {
            Gene g = (Gene) e;
            sb.append(" name=").append(g.getName());
            if (g instanceof SelectableWrapperGene) sb.append(" isActive=").append(((SelectableWrapperGene) g).isActive());
            if (g instanceof ChoiceGene) sb.append(" activeGeneIndex=").append(((ChoiceGene<?>) g).getActiveGeneIndex());
            if (g instanceof EnumGene) sb.append(" values=").append(((EnumGene<?>) g).getValues()).append(" index=").append(((EnumGene<?>) g).getIndex());
            if (g instanceof ArrayGene) sb.append(" elements=").append(((ArrayGene<?>) g).getViewOfElements().size()).append(" minSize=").append(((ArrayGene<?>) g).getMinSize());
            if (g.getViewOfChildren().isEmpty()) {
                try { sb.append(" raw=").append(g.getValueAsRawString()); } catch (Exception ex) { sb.append(" raw=?"); }
            }
        }
        return sb.toString();
    }

    static void print(StructuralElement e, String indent) {
        System.out.println(indent + info(e));
        if (e instanceof ArrayGene) {
            System.out.println(indent + "    (template) " + info(((ArrayGene<?>) e).getTemplate()));
            for (StructuralElement c : ((ArrayGene<?>) e).getTemplate().getViewOfChildren()) print(c, indent + "        ");
        }
        for (StructuralElement c : e.getViewOfChildren()) print(c, indent + "    ");
    }

    static String chain(Gene g) {
        List<String> parts = new ArrayList<>();
        StructuralElement p = g;
        while (p instanceof Gene) {
            String s = p.getClass().getSimpleName() + "(" + ((Gene) p).getName() + ")";
            if (p instanceof SelectableWrapperGene) s += "[isActive=" + ((SelectableWrapperGene) p).isActive() + "]";
            if (p instanceof ChoiceGene) s += "[activeGeneIndex=" + ((ChoiceGene<?>) p).getActiveGeneIndex() + "]";
            parts.add(s);
            p = p.getParent();
        }
        parts.add(p == null ? "null" : p.getClass().getSimpleName());
        return String.join(" <- ", parts);
    }

    static String body(RestCallAction a) {
        for (Param p : a.getParameters()) {
            if (p instanceof BodyParam) {
                return ((BodyParam) p).primaryGene().getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false);
            }
        }
        return "(no body)";
    }

    public static void main(String[] args) throws Exception {
        SchemaOpenAPI s = OpenApiAccess.INSTANCE.parseOpenApi(Files.readString(Path.of(args[0])), SchemaLocation.Companion.getMEMORY());
        EMConfig cfg = new EMConfig();
        cfg.setBlackBox(true);
        Map<String, Action> cluster = new LinkedHashMap<>();
        RestActionBuilderV3.INSTANCE.addActionsFromSwagger(new RestSchema(s), cluster, List.of(), new RestActionBuilderV3.Options(cfg));
        RestCallAction a = (RestCallAction) cluster.get(args[1]).copy();
        a.doInitialize(new Randomness());

        System.out.println("=== cay cua " + args[1] + " sau doInitialize");
        print(a, "");

        System.out.println("=== schemaFields");
        for (RestSecurityBuilder.Companion.SchemaField f : RestSecurityBuilder.Companion.schemaFields(a)) {
            System.out.printf("%-28s gene=%-24s value=%-12s kind=%-6s leaf=%-14s role=%7.3f victim=%7.3f%n",
                    f.getKey(), f.getGene().getClass().getSimpleName(), f.getValue().getClass().getSimpleName(), f.getKind(), f.getLeaf(),
                    RestSecurityBuilder.Companion.fieldScore("role", f), RestSecurityBuilder.Companion.fieldScore("victim", f));
        }
        for (RestSecurityBuilder.Companion.SchemaField f : RestSecurityBuilder.Companion.schemaFields(a)) {
            System.out.println("features " + f.getKey() + " = " + new TreeSet<>(f.features()));
        }
        System.out.printf("transitionScore=%.3f looksLikePermissionReducingTransition=%s%n",
                RestSecurityBuilder.Companion.transitionScore(a), RestSecurityBuilder.Companion.looksLikePermissionReducingTransition(a));

        RestSecurityBuilder b = new RestSecurityBuilder();
        Method bestField = RestSecurityBuilder.class.getDeclaredMethod("bestField", RestCallAction.class, String.class, boolean.class);
        Method victimField = RestSecurityBuilder.class.getDeclaredMethod("victimField", RestCallAction.class);
        Method reduced = RestSecurityBuilder.class.getDeclaredMethod("reducedRoleValues", RestSecurityBuilder.Companion.SchemaField.class, List.class);
        Method setField = RestSecurityBuilder.class.getDeclaredMethod("setField", RestSecurityBuilder.Companion.SchemaField.class, String.class);
        for (Method m : List.of(bestField, victimField, reduced, setField)) m.setAccessible(true);

        RestSecurityBuilder.Companion.SchemaField role = (RestSecurityBuilder.Companion.SchemaField) bestField.invoke(b, a, "role", false);
        RestSecurityBuilder.Companion.SchemaField victim = (RestSecurityBuilder.Companion.SchemaField) victimField.invoke(b, a);
        System.out.println("roleField=" + (role == null ? null : role.getKey()) + " victimField=" + (victim == null ? null : victim.getKey()));
        if (role == null) return;
        @SuppressWarnings("unchecked")
        List<String> values = (List<String>) reduced.invoke(b, role, List.of());
        System.out.println("reducedRoleValues=" + values);

        System.out.println("=== truoc setField");
        int off = 0;
        StructuralElement p = role.getValue().getParent();
        while (p instanceof Gene) {
            if (p instanceof SelectableWrapperGene && ((SelectableWrapperGene) p).isActive()) {
                ((SelectableWrapperGene) p).setActive(false);
                off++;
            }
            p = p.getParent();
        }
        System.out.println("probe tat " + off + " SelectableWrapperGene tren duong len cua truong vai tro");
        System.out.println("chain: " + chain(role.getValue()));
        System.out.println("body:  " + body(a));
        Object ok = setField.invoke(b, role, values.get(0));
        System.out.println("=== setField(" + role.getKey() + ", " + values.get(0) + ") -> " + ok);
        System.out.println("chain: " + chain(role.getValue()));
        System.out.println("body:  " + body(a));
        System.out.println("value raw=" + role.getValue().getValueAsRawString());

        StructuralElement up = role.getValue().getParent();
        while (up instanceof Gene) {
            if (up instanceof NullableGene) {
                ((NullableGene) up).setActive(false);
                System.out.println("=== probe tat NullableGene(" + ((Gene) up).getName() + "), OptionalGene van bat");
                System.out.println("body:  " + body(a));
                ((NullableGene) up).setActive(true);
            }
            up = up.getParent();
        }

        if (args.length > 2 && victim != null) {
            System.out.println("=== truong nan nhan truoc setField");
            StructuralElement q = victim.getValue().getParent();
            while (q instanceof Gene) {
                if (q instanceof ChoiceGene) {
                    ((ChoiceGene<?>) q).selectActiveGene(0);
                    System.out.println("probe chon nhanh 0 cua ChoiceGene(" + ((Gene) q).getName() + ")");
                }
                q = q.getParent();
            }
            System.out.println("chain: " + chain(victim.getValue()));
            System.out.println("resolvedPath: " + a.resolvedPath());
            Object ok2 = setField.invoke(b, victim, args[2]);
            System.out.println("=== setField(" + victim.getKey() + ", " + args[2] + ") -> " + ok2);
            System.out.println("chain: " + chain(victim.getValue()));
            System.out.println("resolvedPath: " + a.resolvedPath());
        }
    }
}
