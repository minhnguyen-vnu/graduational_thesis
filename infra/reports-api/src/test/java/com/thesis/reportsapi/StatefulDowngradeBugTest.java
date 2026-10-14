package com.thesis.reportsapi;

import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;

import java.util.Map;

import static com.thesis.reportsapi.TestSupport.base;
import static com.thesis.reportsapi.TestSupport.bearer;
import static com.thesis.reportsapi.TestSupport.login;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

class StatefulDowngradeBugTest {
    private static SequenceOutcome runSequence(TestRestTemplate rt, int port) {
        rt.postForObject(base(port) + "/reset", null, Map.class);

        String token = login(rt, port, "alice", "alicepass");
        HttpEntity<Void> auth = new HttpEntity<>(bearer(token));

        ResponseEntity<Void> firstDelete = rt.exchange(
                base(port) + "/reports/1", HttpMethod.DELETE, auth, Void.class);
        assertThat(firstDelete.getStatusCode().value()).isEqualTo(204);

        HttpEntity<Map<String, String>> demote = new HttpEntity<>(Map.of("role", "VIEWER"), bearer(token));
        ResponseEntity<Void> demoteResp = rt.exchange(
                base(port) + "/users/alice/role", HttpMethod.PUT, demote, Void.class);
        assertThat(demoteResp.getStatusCode().value()).isEqualTo(200);

        ResponseEntity<Void> secondDelete = rt.exchange(
                base(port) + "/reports/2", HttpMethod.DELETE, auth, Void.class);

        @SuppressWarnings("unchecked")
        Map<String, Object> me = rt.exchange(
                base(port) + "/users/me", HttpMethod.GET, auth, Map.class).getBody();

        return new SequenceOutcome(secondDelete.getStatusCode().value(), (String) me.get("role"));
    }

    private record SequenceOutcome(int secondDeleteStatus, String meRole) {
    }

    @Nested
    @SpringBootTest(webEnvironment = RANDOM_PORT, properties = "app.security.stateful-role-check=false")
    class VulnerableMode {
        @LocalServerPort
        int port;
        @Autowired
        TestRestTemplate rt;

        @Test
        void staleAdminTokenStillDeletesAndMeStillSaysAdmin() {
            SequenceOutcome outcome = runSequence(rt, port);
            assertThat(outcome.secondDeleteStatus()).isEqualTo(204);
            assertThat(outcome.meRole()).isEqualTo("ADMIN");
        }
    }

    @Nested
    @SpringBootTest(webEnvironment = RANDOM_PORT, properties = "app.security.stateful-role-check=true")
    class PatchedMode {
        @LocalServerPort
        int port;
        @Autowired
        TestRestTemplate rt;

        @Test
        void staleAdminTokenIsForbiddenAndMeSaysViewer() {
            SequenceOutcome outcome = runSequence(rt, port);
            assertThat(outcome.secondDeleteStatus()).isEqualTo(403);
            assertThat(outcome.meRole()).isEqualTo("VIEWER");
        }
    }
}
