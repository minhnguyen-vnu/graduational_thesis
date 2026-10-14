package com.thesis.reportsapi;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;

import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import static com.thesis.reportsapi.TestSupport.base;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

@SpringBootTest(webEnvironment = RANDOM_PORT)
class OpenApiContractTest {

    private static final Map<String, Set<String>> EXPECTED_RESPONSES = Map.of(
            "POST /auth/login", Set.of("200", "400", "401"),
            "POST /reset", Set.of("200"),
            "GET /reports", Set.of("200", "401"),
            "POST /reports", Set.of("201", "400", "401", "403"),
            "GET /reports/{id}", Set.of("200", "400", "401", "404"),
            "PUT /reports/{id}", Set.of("200", "400", "401", "403", "404"),
            "DELETE /reports/{id}", Set.of("204", "400", "401", "403", "404"),
            "GET /users/me", Set.of("200", "401"),
            "PUT /users/{username}/role", Set.of("200", "400", "401", "403", "404"));

    @LocalServerPort
    int port;
    @Autowired
    TestRestTemplate rt;

    private JsonNode spec() throws Exception {
        return new ObjectMapper().readTree(rt.getForObject(base(port) + "/v3/api-docs", String.class));
    }

    @Test
    void noOperationExposesTheCurrentUserArgument() throws Exception {
        List<String> offenders = new ArrayList<>();
        JsonNode paths = spec().get("paths");
        paths.fieldNames().forEachRemaining(path ->
                paths.get(path).fieldNames().forEachRemaining(verb -> {
                    JsonNode params = paths.get(path).get(verb).get("parameters");
                    if (params != null) {
                        params.forEach(p -> {
                            if ("caller".equals(p.get("name").asText())) {
                                offenders.add(verb.toUpperCase() + " " + path);
                            }
                        });
                    }
                }));
        assertThat(offenders).isEmpty();
    }

    @Test
    void currentUserIsNotAPublishedSchema() throws Exception {
        assertThat(spec().get("components").get("schemas").has("CurrentUser")).isFalse();
    }

    @Test
    void roleUpdateRequestDeclaresItsAllowedValues() throws Exception {
        JsonNode role = spec().get("components").get("schemas")
                .get("RoleUpdateRequest").get("properties").get("role");
        Set<String> values = new LinkedHashSet<>();
        role.get("enum").forEach(v -> values.add(v.asText()));
        assertThat(values).containsExactlyInAnyOrder("ADMIN", "VIEWER");
    }

    @Test
    void everyOperationDeclaresExactlyTheStatusesItCanReturn() throws Exception {
        Map<String, Set<String>> actual = declaredResponses(spec());
        assertThat(actual).isEqualTo(EXPECTED_RESPONSES);
    }

    @Test
    void noOperationDeclaresAServerError() throws Exception {
        declaredResponses(spec()).forEach((op, codes) -> assertThat(codes).doesNotContain("500"));
    }

    private static Map<String, Set<String>> declaredResponses(JsonNode spec) {
        Map<String, Set<String>> declared = new java.util.LinkedHashMap<>();
        JsonNode paths = spec.get("paths");
        paths.fieldNames().forEachRemaining(path ->
                paths.get(path).fieldNames().forEachRemaining(verb -> {
                    Set<String> codes = new TreeSet<>();
                    paths.get(path).get(verb).get("responses").fieldNames().forEachRemaining(codes::add);
                    declared.put(verb.toUpperCase() + " " + path, codes);
                }));
        return declared;
    }
}
