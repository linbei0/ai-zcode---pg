package com.aizcode;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.EnableAspectJAutoProxy;

@SpringBootApplication
@EnableAspectJAutoProxy(exposeProxy = true)
public class AiZcodeApplication {

    public static void main(String[] args) {
        SpringApplication.run(AiZcodeApplication.class, args);
    }

}
