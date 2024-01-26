#version 330 core

out vec4 FragColor;

struct PointLight {
    vec3 position;
    
    float constant;
    float linear;
    float quadratic;
	
    vec3 ambient;
    vec3 diffuse;
    vec3 specular;
};

uniform vec3 lightColor;
  
void main()
{
    FragColor = max(vec4(lightColor,1),0.1);
}