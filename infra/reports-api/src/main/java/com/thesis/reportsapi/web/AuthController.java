package com.thesis.reportsapi.web;

import com.thesis.reportsapi.dto.ErrorResponse;
import com.thesis.reportsapi.dto.LoginRequest;
import com.thesis.reportsapi.dto.LoginResponse;
import com.thesis.reportsapi.model.User;
import com.thesis.reportsapi.security.ApiException;
import com.thesis.reportsapi.security.JwtService;
import com.thesis.reportsapi.store.UserStore;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.Optional;

@RestController
public class AuthController {
    private final UserStore userStore;
    private final JwtService jwtService;

    public AuthController(UserStore userStore, JwtService jwtService) {
        this.userStore = userStore;
        this.jwtService = jwtService;
    }

    @PostMapping("/auth/login")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "token issued"),
            @ApiResponse(responseCode = "400", description = "invalid request body",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "401", description = "invalid credentials",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public LoginResponse login(@Valid @RequestBody LoginRequest request) {
        Optional<User> found = userStore.findByUsername(request.username());
        if (found.isEmpty() || !found.get().password().equals(request.password())) {
            throw new ApiException.Unauthorized("invalid credentials");
        }
        User user = found.get();
        String token = jwtService.mint(user.username(), user.role());
        return new LoginResponse(token, user.username(), user.role());
    }
}
