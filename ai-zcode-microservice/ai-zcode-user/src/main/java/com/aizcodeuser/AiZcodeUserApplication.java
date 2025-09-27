package com.aizcodeuser;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@MapperScan("com.aizcodeuser.mapper")
//@ComponentScan("com")
public class AiZcodeUserApplication {
    public static void main(String[] args) {
        SpringApplication.run(AiZcodeUserApplication.class, args);
    }
}