package com.thesis.reportsapi.web;

import com.thesis.reportsapi.dto.ErrorResponse;
import com.thesis.reportsapi.dto.MeResponse;
import com.thesis.reportsapi.dto.RoleResponse;
import com.thesis.reportsapi.dto.RoleUpdateRequest;
import com.thesis.reportsapi.model.Role;
import com.thesis.reportsapi.model.User;
import com.thesis.reportsapi.security.ApiException;
import com.thesis.reportsapi.security.Authz;
import com.thesis.reportsapi.security.CurrentUser;
import com.thesis.reportsapi.store.UserStore;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class UserController {
    private final UserStore userStore;

    public UserController(UserStore userStore) {
        this.userStore = userStore;
    }

    @PutMapping("/users/{username}/role")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "role updated"),
            @ApiResponse(responseCode = "400", description = "invalid role value",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "403", description = "admin role required",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class))),
            @ApiResponse(responseCode = "404", description = "no such user",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public RoleResponse changeRole(@PathVariable String username,
                                   @Valid @RequestBody RoleUpdateRequest request,
                                   CurrentUser caller) {
        Authz.requireAdmin(caller);

        Role newRole = parseRole(request.role());
        userStore.findByUsername(username)
                .orElseThrow(() -> new ApiException.NotFound("user not found"));

        User updated = userStore.updateRole(username, newRole);
        return new RoleResponse(updated.username(), updated.role());
    }

    @GetMapping("/users/me")
    @ApiResponses({
            @ApiResponse(responseCode = "200", description = "the authenticated user"),
            @ApiResponse(responseCode = "401", description = "missing or invalid token",
                    content = @Content(mediaType = "application/json",
                            schema = @Schema(implementation = ErrorResponse.class)))
    })
    public MeResponse me(CurrentUser caller) {
        return new MeResponse(caller.username(), caller.effectiveRole());
    }

    private Role parseRole(String raw) {
        try {
            return Role.valueOf(raw);
        } catch (IllegalArgumentException | NullPointerException ex) {
            throw new ApiException.BadRequest("invalid role");
        }
    }
}
