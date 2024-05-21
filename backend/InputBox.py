import pygame
import time

class InputBox:
    def __init__(self):
        self.text = ""
        self.font = pygame.font.SysFont('Arial', 25)
        self.activeInput = None
        self.lastInputClick = 0
        self.inputCooldown = 0.5  # Cooldown time to prevent rapid state changes
        self.active = False
        self.isClicked = True

    def inputBox(self, x, y, onlineMenuOffset, width, height, placeholder, text, surface, active=False):
        mouse = pygame.mouse.get_pos()
        click = pygame.mouse.get_pressed()

        # Draw the input box
        boxColor = (200, 200, 200) if active else (255, 255, 255)
        pygame.draw.rect(surface, boxColor, (x, y, width, height), border_radius=10)

        # Render the text
        # font = pygame.font.SysFont('Arial', 25)
        if text or self.active:
            self.text = text
            self.textSurface = self.font.render(self.text, True, (0, 0, 0))
        else:
            self.textSurface = self.font.render(placeholder, True, (150, 150, 150))
        surface.blit(self.textSurface, (x + 10, y + height / 2 - self.textSurface.get_height() / 2))

        # Check if the mouse is inside the hitbox
        if mouse[0] >= x + onlineMenuOffset[0] and mouse[0] <= x + onlineMenuOffset[0] + width and mouse[1] >= y + onlineMenuOffset[1] and mouse[1] <= y + onlineMenuOffset[1] + height:
            if click[0] == 1 and time.time() - self.lastInputClick > self.inputCooldown:
                self.isClicked = True
                # print("Inside")
                self.lastInputClick = time.time()
            
    def handle_event(self, event, active):
        if active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]  # Remove the last character
                else:
                    self.text += event.unicode  # Add the character typed
