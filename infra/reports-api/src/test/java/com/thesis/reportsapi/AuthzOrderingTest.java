package com.thesis.reportsapi;

import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Map;

import static com.thesis.reportsapi.TestSupport.base;
import static com.thesis.reportsapi.TestSupport.bearer;
import static com.thesis.reportsapi.TestSupport.login;
import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

@SpringBootTest(webEnvironment = RANDOM_PORT)
class AuthzOrderingTest {
    private static final String SECRET = "dev-only-change-me-please-32bytes-min";

    @LocalServerPort
    int port;
    @Autowired
    TestRestTemplate rt;

    @BeforeEach
    void reset() {
        rt.postForObject(base(port) + "/reset", null, Map.class);
    }

    @Test
    void noTokenIsUnauthorized() {
        int status = rt.exchange(base(port) + "/reports", HttpMethod.GET,
                HttpEntity.EMPTY, String.class).getStatusCode().value();
        assertThat(status).isEqualTo(401);
    }

    @Test
    void garbageTokenIsUnauthorized() {
        int status = rt.exchange(base(port) + "/reports", HttpMethod.GET,
                new HttpEntity<>(bearer("not-a-real-jwt")), String.class).getStatusCode().value();
        assertThat(status).isEqualTo(401);
    }

    @Test
    void expiredTokenIsUnauthorized() {
        int status = rt.exchange(base(port) + "/reports", HttpMethod.GET,
                new HttpEntity<>(bearer(expiredToken())), String.class).getStatusCode().value();
        assertThat(status).isEqualTo(401);
    }

    @Test
    void viewerDeletingUnknownIdGets403Not404() {
        String bob = login(rt, port, "bob", "bobpass");
        int status = rt.exchange(base(port) + "/reports/999", HttpMethod.DELETE,
                new HttpEntity<>(bearer(bob)), String.class).getStatusCode().value();
        assertThat(status).isEqualTo(403);
    }

    @Test
    void adminDeletingUnknownIdGets404() {
        String alice = login(rt, port, "alice", "alicepass");
        int status = rt.exchange(base(port) + "/reports/999", HttpMethod.DELETE,
                new HttpEntity<>(bearer(alice)), String.class).getStatusCode().value();
        assertThat(status).isEqualTo(404);
    }

    private static String expiredToken() {
        SecretKey key = Keys.hmacShaKeyFor(SECRET.getBytes(StandardCharsets.UTF_8));
        Instant now = Instant.now();
        return Jwts.builder()
                .subject("alice")
                .claim("role", "ADMIN")
                .issuedAt(Date.from(now.minusSeconds(7200)))
                .expiration(Date.from(now.minusSeconds(3600)))
                .signWith(key)
                .compact();
    }
}
