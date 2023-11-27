#version 330 core

layout (location=0) in vec3 vertexPos;
layout (location=1) in vec2 vertexTexCoord;
layout (location=2) in vec3 vertexColor;

out vec3 fragmentColor;
out vec2 fragmentTexCoord;

void main()
{
    gl_Position = vec4(vertexPos, 1.0);
    vec3 vertColor = vertexColor;
    fragmentColor = vertColor;
    fragmentTexCoord = vertexTexCoord;
}