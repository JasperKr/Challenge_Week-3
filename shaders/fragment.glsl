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
    float focus;
    vec2 direction;
};

const int PointLightsAmount = 10;
const int SpotLightsAmount = 10;

out vec4 color;

uniform sampler2D imageTexture;
uniform PointLight[PointLightsAmount] PointLights;
uniform SpotLight[SpotLightsAmount] SpotLights;
uniform vec2 CameraPosition;

vec3 evaluateLights(vec2 pos) {
    vec3 incomingLight = vec3(0.0);
    for (int i = 0; i < PointLightsAmount; i++) {
        PointLight light = PointLights[i];
        vec2 difference = pos - light.position;
        float dist = length(difference);
        dist /= light.radius;
        float attenuation = 1.0 / (dist * dist);

        incomingLight += attenuation * light.color;
    }
    for (int i = 0; i < SpotLightsAmount; i++) {
        SpotLight light = SpotLights[i];

        vec2 L = pos - light.position;

        float dist = length(L);
        dist /= light.range;
        float attenuation = 1.0 / (dist * dist);

        float theta = dot(L, normalize(-light.direction));
        float innerCutOff = radians(light.focus);
        float outerCutOff = radians(light.focus + 15);
        float epsilon = max(outerCutOff - innerCutOff, 0.00001 );
        float intensity = 1-clamp((outerCutOff - theta) / epsilon, 0.0, 1.0);   

        incomingLight += intensity * light.color * attenuation;
    }

    return incomingLight;
}

void main() {
    vec3 lightIntensity = evaluateLights(fragmentTexCoord * vec2(1280, 720) - CameraPosition) + 0.2;
    color = texture(imageTexture, fragmentTexCoord) * vec4(lightIntensity, 1.0);// * vec4(fragmentTexCoord, 0.0, 1.0);
}