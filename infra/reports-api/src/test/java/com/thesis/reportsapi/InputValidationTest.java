package com.thesis.reportsapi;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

@SpringBootTest(webEnvironment = RANDOM_PORT)
class InputValidationTest {

    private final HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5)).build();

    @LocalServerPort
    int port;

    private String alice;

    @BeforeEach
    void reset() throws Exception {
        send("POST", "/reset", null, null);
        alice = token("alice", "alicepass");
    }

    private HttpResponse<String> send(String method, String path, String json, String bearer) throws Exception {
        HttpRequest.BodyPublisher body = json == null
                ? HttpRequest.BodyPublishers.noBody()
                : HttpRequest.BodyPublishers.ofString(json);
        HttpRequest.Builder request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:" + port + path))
                .header("Content-Type", "application/json")
                .method(method, body);
        if (bearer != null) {
            request.header("Authorization", "Bearer " + bearer);
        }
        return client.send(request.build(), HttpResponse.BodyHandlers.ofString());
    }

    private String token(String username, String password) throws Exception {
        HttpResponse<String> res = send("POST", "/auth/login",
                "{\"username\":\"" + username + "\",\"password\":\"" + password + "\"}", null);
        assertThat(res.statusCode()).isEqualTo(200);
        return res.body().replaceAll(".*\"token\"\\s*:\\s*\"([^\"]+)\".*", "$1");
    }

    @Test
    void loginWithoutUsernameIsBadRequestNotServerError() throws Exception {
        HttpResponse<String> res = send("POST", "/auth/login", "{\"password\":\"x\"}", null);
        assertThat(res.statusCode()).isEqualTo(400);
        assertThat(res.body()).contains("\"error\"");
    }

    @Test
    void loginWithBlankPasswordIsBadRequest() throws Exception {
        assertThat(send("POST", "/auth/login", "{\"username\":\"alice\",\"password\":\"\"}", null)
                .statusCode()).isEqualTo(400);
    }

    @Test
    void loginWithUnknownUserIsUnauthorized() throws Exception {
        assertThat(send("POST", "/auth/login", "{\"username\":\"nobody\",\"password\":\"x\"}", null)
                .statusCode()).isEqualTo(401);
    }

    @Test
    void createReportWithEmptyBodyIsBadRequest() throws Exception {
        assertThat(send("POST", "/reports", "{}", alice).statusCode()).isEqualTo(400);
    }

    @Test
    void createReportWithoutClassificationIsBadRequest() throws Exception {
        assertThat(send("POST", "/reports", "{\"title\":\"x\"}", alice).statusCode()).isEqualTo(400);
    }

    @Test
    void createReportWithValidBodyIsCreated() throws Exception {
        assertThat(send("POST", "/reports", "{\"title\":\"x\",\"classification\":\"PUBLIC\"}", alice)
                .statusCode()).isEqualTo(201);
    }

    @Test
    void malformedJsonIsBadRequest() throws Exception {
        assertThat(send("POST", "/reports", "{not json", alice).statusCode()).isEqualTo(400);
    }

    @Test
    void malformedReportIdIsBadRequest() throws Exception {
        assertThat(send("GET", "/reports/abc", null, alice).statusCode()).isEqualTo(400);
    }

    @Test
    void blankRoleIsBadRequest() throws Exception {
        assertThat(send("PUT", "/users/alice/role", "{\"role\":\"\"}", alice).statusCode()).isEqualTo(400);
    }

    @Test
    void lowercaseRoleIsRejected() throws Exception {
        HttpResponse<String> res = send("PUT", "/users/alice/role", "{\"role\":\"viewer\"}", alice);
        assertThat(res.statusCode()).isEqualTo(400);
        assertThat(res.body()).contains("invalid role");
    }

    @Test
    void declaredRoleValueIsAccepted() throws Exception {
        assertThat(send("PUT", "/users/alice/role", "{\"role\":\"VIEWER\"}", alice).statusCode())
                .isEqualTo(200);
    }

    @Test
    void unknownUserRoleChangeIsNotFound() throws Exception {
        assertThat(send("PUT", "/users/nobody/role", "{\"role\":\"VIEWER\"}", alice).statusCode())
                .isEqualTo(404);
    }

    @Test
    void viewerWithValidBodyStillGetsForbidden() throws Exception {
        String bob = token("bob", "bobpass");
        assertThat(send("POST", "/reports", "{\"title\":\"x\",\"classification\":\"PUBLIC\"}", bob)
                .statusCode()).isEqualTo(403);
    }

    @Test
    void noRequestEverReturnsServerError() throws Exception {
        String[][] cases = {
                {"POST", "/auth/login", "{}"},
                {"POST", "/auth/login", "null"},
                {"POST", "/reports", "{\"title\":null,\"classification\":null}"},
                {"PUT", "/reports/1", "{}"},
                {"PUT", "/users/alice/role", "{\"role\":null}"},
                {"GET", "/reports/-1", null},
        };
        for (String[] c : cases) {
            assertThat(send(c[0], c[1], c[2], alice).statusCode())
                    .as(c[0] + " " + c[1] + " " + c[2]).isLessThan(500);
        }
    }
}
