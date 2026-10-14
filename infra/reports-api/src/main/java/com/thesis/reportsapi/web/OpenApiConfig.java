package com.thesis.reportsapi.web;

import com.thesis.reportsapi.security.CurrentUser;
import org.springdoc.core.utils.SpringDocUtils;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {
    static {
        SpringDocUtils.getConfig().addRequestWrapperToIgnore(CurrentUser.class);
    }
}
