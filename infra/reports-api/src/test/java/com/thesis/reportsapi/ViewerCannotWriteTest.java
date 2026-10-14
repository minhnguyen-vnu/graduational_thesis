package com.thesis.reportsapi;

import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;

import java.util.Map;

import static com.thesis.reportsapi.TestSupport.base;
import static com.thesis.reportsapi.TestSupport.bearer;
import static com.thesis.reportsapi.TestSupport.login;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

class ViewerCannotWriteTest {
    private static void assertBobForbiddenOnAllWrites(TestRestTemplate rt, int port) {
        rt.postForObject(base(port) + "/reset", null, Map.class);
        String token = login(rt, port, "bob", "bobpass");

        HttpEntity<Map<String, String>> withBody =
                new HttpEntity<>(Map.of("title", "x", "classification", "PUBLIC"), bearer(token));
        HttpEntity<Void> noBody = new HttpEntity<>(bearer(token));

        int post = rt.exchange(base(port) + "/reports", HttpMethod.POST, withBody, String.class)
                .getStatusCode().value();
        int put = rt.exchange(base(port) + "/reports/1", HttpMethod.PUT, withBody, String.class)
                .getStatusCode().value();
        int delete = rt.exchange(base(port) + "/reports/1", HttpMethod.DELETE, noBody, String.class)
                .getStatusCode().value();

        assertThat(post).isEqualTo(403);
        assertThat(put).isEqualTo(403);
        assertThat(delete).isEqualTo(403);
    }

    @Nested
    @SpringBootTest(webEnvironment = RANDOM_PORT, properties = "app.security.stateful-role-check=false")
    class VulnerableMode {
        @LocalServerPort
        int port;
        @Autowired
        TestRestTemplate rt;

        @Test
        void viewerForbiddenOnWrites() {
            assertBobForbiddenOnAllWrites(rt, port);
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
        void viewerForbiddenOnWrites() {
            assertBobForbiddenOnAllWrites(rt, port);
        }
    }
}
