import org.evomaster.core.EMConfig;
import org.evomaster.core.problem.rest.schema.*;
import org.evomaster.core.problem.rest.builder.RestActionBuilderV3;
import org.evomaster.core.problem.rest.data.*;
import org.evomaster.core.problem.rest.param.*;
import org.evomaster.core.search.action.*;
import org.evomaster.core.search.gene.*;
import org.evomaster.core.search.gene.string.StringGene;
import org.evomaster.core.search.gene.collection.EnumGene;
import org.evomaster.core.search.gene.utils.GeneUtils;
import org.evomaster.core.search.service.Randomness;
import java.nio.file.*;
import java.util.*;

public class Genes {
    public static void main(String[] args) throws Exception {
        SchemaOpenAPI s = OpenApiAccess.INSTANCE.parseOpenApi(Files.readString(Path.of(args[0])), SchemaLocation.Companion.getMEMORY());
        EMConfig cfg = new EMConfig(); cfg.setBlackBox(true);
        Map<String, Action> cluster = new LinkedHashMap<>();
        RestActionBuilderV3.INSTANCE.addActionsFromSwagger(new RestSchema(s), cluster, List.of(), new RestActionBuilderV3.Options(cfg));
        RestCallAction a = (RestCallAction) cluster.get("POST:/reports").copy();
        System.out.println("before doInitialize: initialized=" + a.isInitialized());
        a.doInitialize(new Randomness());
        BodyParam bp = (BodyParam) a.getParameters().get(0);
        System.out.println("BodyParam.name=" + bp.getName() + " genes.size=" + bp.seeGenes().size() + " primaryGene=" + bp.primaryGene().getClass().getSimpleName());
        ObjectGene body = (ObjectGene) bp.primaryGene();
        StringGene title = (StringGene) body.getViewOfChildren().get(0);
        EnumGene<?> cls = (EnumGene<?>) body.getViewOfChildren().get(1);
        System.out.println("title.value after random init=" + title.getValue() + " cls.values=" + cls.getValues() + " cls.index=" + cls.getIndex());
        title.setFromStringValue("8nI4Cb1ZO", true);
        cls.setFromStringValue("PUBLIC", true);
        System.out.println("title.value=" + title.getValue() + " cls.index=" + cls.getIndex());
        System.out.println("title.printable(JSON)=" + title.getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false) + " raw=" + title.getValueAsRawString());
        System.out.println("cls.printable(JSON)=" + cls.getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false) + " raw=" + cls.getValueAsRawString());
        System.out.println("body.printable(JSON)=" + body.getValueAsPrintableString(List.of(), GeneUtils.EscapeMode.JSON, null, false));
        System.out.println("title.parent=" + title.getParent().getClass().getSimpleName() + "(" + ((Gene) title.getParent()).getName() + ") root=" + title.getRoot().getClass().getSimpleName());
        System.out.println("body.flatView=" + body.flatView(g -> false).stream().map(g -> g.getClass().getSimpleName() + ":" + g.getName()).toList());
        System.out.println("a.seeTopGenes=" + a.seeTopGenes().stream().map(g -> g.getClass().getSimpleName() + ":" + g.getName()).toList());
        System.out.println("a.seeAllGenes.size=" + a.seeAllGenes().size());
        Gene copy = body.copy();
        ((StringGene) copy.getViewOfChildren().get(0)).setValue("changed");
        System.out.println("after changing copy: original title=" + title.getValue() + " copy title=" + ((StringGene) copy.getViewOfChildren().get(0)).getValue());
        RestCallAction put = (RestCallAction) cluster.get("PUT:/users/{username}/role").copy();
        put.doInitialize(new Randomness());
        PathParam pp = (PathParam) put.getParameters().get(0);
        System.out.println("PathParam primaryGene=" + pp.primaryGene().getClass().getSimpleName() + " child=" + pp.primaryGene().getViewOfChildren().get(0).getClass().getSimpleName() + " probability=" + ((org.evomaster.core.search.gene.wrapper.CustomMutationRateGene<?>) pp.primaryGene()).getProbability());
        System.out.println("put.path=" + put.getPath() + " resolvedPath before=" + put.resolvedPath());
        pp.primaryGene().setFromStringValue("superadmin", true);
        System.out.println("resolvedPath after=" + put.resolvedPath() + " path unchanged=" + put.getPath());
    }
}
