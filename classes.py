class player():
    def __init__(self, position=[0.0, 0.0], radius=1.0, drag=0.1) -> None:
        self.position = position
        self.radius = radius
        self.velocity = [0.0, 0.0]
        self.drag = drag
