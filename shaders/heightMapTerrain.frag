#version 330 core

out vec4 FragColor;

in float Height;

void main()
{
    float h = (Height + 10)/32.0;	// shift and scale the height in to a grayscale value
    if(h < 0.1) {
        FragColor = vec4(0.2,0.5,0.8,1.0);
    }
    else {
        FragColor = vec4(0.1, h, 0.1, 1.0);
    }
}