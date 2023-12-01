#version 330 core

layout (location=0) in vec3 vertexPos;
layout (location=1) in vec2 vertexTexCoord;
layout (location=2) in vec3 vertexColor;

out vec3 fragmentColor;
out vec2 fragmentTexCoord;

const vec2 screenSize = vec2(1280.0, 720.0);
const vec2 center = screenSize / 2.0;
const vec2 inverseScreenSize = vec2(1.0 / 1280.0, 1.0 / 720.0);

void main()
{
    gl_Position = vec4(vertexPos, 1.0);
    vec3 vertColor = vertexColor;
    fragmentColor = vertColor;
    fragmentTexCoord = vertexTexCoord;
}