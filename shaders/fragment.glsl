#version 330 core

in vec3 fragmentColor;
in vec2 fragmentTexCoord;

struct PointLight {
    vec2 position;
    float radius;
    vec3 color;
};

struct SpotLight {
    vec2 position;
    float range;
    vec3 color;
    vec2 falloffAngles;
    vec2 direction;
};

const int PointLightsAmount = 10;
const int SpotLightsAmount = 10;

out vec4 color;

uniform sampler2D imageTexture;
uniform PointLight[PointLightsAmount] PointLights;

//vec3 evaluateLights(vec2 pos, )

void main() {
    color = texture(imageTexture, fragmentTexCoord);// * vec4(fragmentTexCoord, 0.0, 1.0);
}