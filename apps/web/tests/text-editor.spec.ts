import { test, expect } from '@playwright/test';

/**
 * TextEditor Component UI Automation Tests
 *
 * Tests the following functionality:
 * 1. Font size slider and number input synchronization
 * 2. Large number input handling (e.g., "180")
 * 3. Color picker state persistence
 * 4. Layer switching behavior
 */

test.describe('TextEditor - Font Size Controls', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');

    // Wait for the app to load
    await page.waitForLoadState('networkidle');

    // Create a test text layer by clicking "Add Text" button
    const addTextButton = page.locator('button:has-text("添加文本"), button:has-text("Add Text")').first();
    if (await addTextButton.isVisible()) {
      await addTextButton.click();
      await page.waitForTimeout(500);
    }
  });

  test('slider changes should update number input display', async ({ page }) => {
    // Locate the font size slider
    const slider = page.locator('input[type="range"][min="12"][max="200"]');
    await expect(slider).toBeVisible();

    // Locate the number input
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');
    await expect(numberInput).toBeVisible();

    // Get initial value
    const initialValue = await numberInput.inputValue();
    console.log(`Initial font size: ${initialValue}`);

    // Drag slider to 60px
    await slider.fill('60');
    await page.waitForTimeout(300);

    // Check that number input displays 60
    const sliderUpdatedValue = await numberInput.inputValue();
    console.log(`After slider to 60: ${sliderUpdatedValue}`);
    expect(sliderUpdatedValue).toBe('60');

    // Drag slider to 120px
    await slider.fill('120');
    await page.waitForTimeout(300);

    // Check that number input displays 120
    const sliderUpdatedValue2 = await numberInput.inputValue();
    console.log(`After slider to 120: ${sliderUpdatedValue2}`);
    expect(sliderUpdatedValue2).toBe('120');
  });

  test('number input changes should update slider position', async ({ page }) => {
    const slider = page.locator('input[type="range"][min="12"][max="200"]');
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');

    // Focus number input and type 80
    await numberInput.click();
    await numberInput.fill('80');
    await numberInput.blur();
    await page.waitForTimeout(300);

    // Check slider value
    const sliderValue = await slider.inputValue();
    console.log(`After number input to 80: slider = ${sliderValue}`);
    expect(sliderValue).toBe('80');
  });

  test('number input should accept large values like 180', async ({ page }) => {
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');

    // Click to focus
    await numberInput.click();

    // Clear and type 180 character by character
    await numberInput.fill('');
    await numberInput.pressSequentially('180', { delay: 100 });

    // Wait a moment to ensure state updates
    await page.waitForTimeout(200);

    // Check that the input shows "180" BEFORE blur
    const valueDuringEdit = await numberInput.inputValue();
    console.log(`Value during edit: ${valueDuringEdit}`);
    expect(valueDuringEdit).toBe('180');

    // Blur (apply changes)
    await numberInput.blur();
    await page.waitForTimeout(300);

    // Check that value persists after blur
    const valueAfterBlur = await numberInput.inputValue();
    console.log(`Value after blur: ${valueAfterBlur}`);
    expect(valueAfterBlur).toBe('180');

    // Check that slider also updated
    const slider = page.locator('input[type="range"][min="12"][max="200"]');
    const sliderValue = await slider.inputValue();
    console.log(`Slider value after 180 input: ${sliderValue}`);
    expect(sliderValue).toBe('180');
  });

  test('pressing Enter should apply number input changes', async ({ page }) => {
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');
    const slider = page.locator('input[type="range"][min="12"][max="200"]');

    await numberInput.click();
    await numberInput.fill('150');
    await numberInput.press('Enter');
    await page.waitForTimeout(300);

    const numberValue = await numberInput.inputValue();
    const sliderValue = await slider.inputValue();

    console.log(`After Enter: number=${numberValue}, slider=${sliderValue}`);
    expect(numberValue).toBe('150');
    expect(sliderValue).toBe('150');
  });

  test('pressing Escape should cancel number input changes', async ({ page }) => {
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');

    // Get initial value
    const initialValue = await numberInput.inputValue();
    console.log(`Initial value: ${initialValue}`);

    // Start editing
    await numberInput.click();
    await numberInput.fill('99');

    // Press Escape to cancel
    await numberInput.press('Escape');
    await page.waitForTimeout(300);

    // Should revert to initial value
    const valueAfterEscape = await numberInput.inputValue();
    console.log(`After Escape: ${valueAfterEscape}`);
    expect(valueAfterEscape).toBe(initialValue);
  });

  test('values should clamp to min/max range', async ({ page }) => {
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');
    const slider = page.locator('input[type="range"][min="12"][max="200"]');

    // Test max boundary (201 should clamp to 200)
    await numberInput.click();
    await numberInput.fill('250');
    await numberInput.blur();
    await page.waitForTimeout(300);

    let clampedValue = await numberInput.inputValue();
    console.log(`After entering 250: ${clampedValue}`);
    expect(clampedValue).toBe('200');

    // Test min boundary (5 should clamp to 12)
    await numberInput.click();
    await numberInput.fill('5');
    await numberInput.blur();
    await page.waitForTimeout(300);

    clampedValue = await numberInput.inputValue();
    console.log(`After entering 5: ${clampedValue}`);
    expect(clampedValue).toBe('12');
  });
});

test.describe('TextEditor - Color Picker Persistence', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const addTextButton = page.locator('button:has-text("添加文本"), button:has-text("Add Text")').first();
    if (await addTextButton.isVisible()) {
      await addTextButton.click();
      await page.waitForTimeout(500);
    }
  });

  test('color should persist when adjusting font size with slider', async ({ page }) => {
    const colorInput = page.locator('input[type="color"]');
    const slider = page.locator('input[type="range"][min="12"][max="200"]');

    // Set color to red
    await colorInput.fill('#ff0000');
    await page.waitForTimeout(300);

    const colorAfterSet = await colorInput.inputValue();
    console.log(`Color after setting to red: ${colorAfterSet}`);
    expect(colorAfterSet.toLowerCase()).toBe('#ff0000');

    // Drag font size slider
    await slider.fill('80');
    await page.waitForTimeout(300);

    // Color should still be red
    const colorAfterSlider = await colorInput.inputValue();
    console.log(`Color after slider change: ${colorAfterSlider}`);
    expect(colorAfterSlider.toLowerCase()).toBe('#ff0000');
  });

  test('color should persist when adjusting font size with number input', async ({ page }) => {
    const colorInput = page.locator('input[type="color"]');
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');

    // Set color to blue
    await colorInput.fill('#0000ff');
    await page.waitForTimeout(300);

    // Change font size via number input
    await numberInput.click();
    await numberInput.fill('100');
    await numberInput.blur();
    await page.waitForTimeout(300);

    // Color should still be blue
    const colorAfterFontChange = await colorInput.inputValue();
    console.log(`Color after font size change: ${colorAfterFontChange}`);
    expect(colorAfterFontChange.toLowerCase()).toBe('#0000ff');
  });

  test('color should persist through multiple rapid changes', async ({ page }) => {
    const colorInput = page.locator('input[type="color"]');
    const slider = page.locator('input[type="range"][min="12"][max="200"]');
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');
    const fontWeightSelect = page.locator('select').first();

    // Set color to green
    await colorInput.fill('#00ff00');
    await page.waitForTimeout(200);

    // Rapid changes
    await slider.fill('60');
    await page.waitForTimeout(100);

    await numberInput.click();
    await numberInput.fill('120');
    await numberInput.blur();
    await page.waitForTimeout(100);

    if (await fontWeightSelect.isVisible()) {
      await fontWeightSelect.selectOption('700');
      await page.waitForTimeout(100);
    }

    // Color should still be green
    const finalColor = await colorInput.inputValue();
    console.log(`Color after rapid changes: ${finalColor}`);
    expect(finalColor.toLowerCase()).toBe('#00ff00');
  });
});

test.describe('TextEditor - Layer Switching', () => {
  test('switching layers should show correct font size values', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Create two text layers
    const addTextButton = page.locator('button:has-text("添加文本"), button:has-text("Add Text")').first();

    // Add first text layer
    await addTextButton.click();
    await page.waitForTimeout(500);

    // Set font size to 48
    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');
    await numberInput.click();
    await numberInput.fill('48');
    await numberInput.blur();
    await page.waitForTimeout(300);

    // Add second text layer
    await addTextButton.click();
    await page.waitForTimeout(500);

    // Set font size to 96
    await numberInput.click();
    await numberInput.fill('96');
    await numberInput.blur();
    await page.waitForTimeout(300);

    const layer2Value = await numberInput.inputValue();
    console.log(`Layer 2 font size: ${layer2Value}`);
    expect(layer2Value).toBe('96');

    // Switch back to first layer (click on layer panel)
    const layerPanelItems = page.locator('.layer-panel .layer-item');
    const layerCount = await layerPanelItems.count();

    if (layerCount >= 2) {
      await layerPanelItems.nth(0).click();
      await page.waitForTimeout(300);

      // Should show 48
      const layer1Value = await numberInput.inputValue();
      console.log(`Layer 1 font size after switching back: ${layer1Value}`);
      expect(layer1Value).toBe('48');

      // Switch to second layer again
      await layerPanelItems.nth(1).click();
      await page.waitForTimeout(300);

      // Should show 96
      const layer2ValueAgain = await numberInput.inputValue();
      console.log(`Layer 2 font size after switching again: ${layer2ValueAgain}`);
      expect(layer2ValueAgain).toBe('96');
    }
  });

  test('editing state should reset when switching layers', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const addTextButton = page.locator('button:has-text("添加文本"), button:has-text("Add Text")').first();

    // Create two layers
    await addTextButton.click();
    await page.waitForTimeout(500);
    await addTextButton.click();
    await page.waitForTimeout(500);

    const numberInput = page.locator('input[type="number"][min="12"][max="200"]');

    // Start editing layer 2
    await numberInput.click();
    await numberInput.fill('150');
    // DON'T blur - leave in editing state

    await page.waitForTimeout(200);

    // Switch to layer 1
    const layerPanelItems = page.locator('.layer-panel .layer-item');
    if ((await layerPanelItems.count()) >= 2) {
      await layerPanelItems.nth(0).click();
      await page.waitForTimeout(300);

      // Number input should show layer 1's value, not "150"
      const layer1Value = await numberInput.inputValue();
      console.log(`Layer 1 value after switching during edit: ${layer1Value}`);
      expect(layer1Value).not.toBe('150');
    }
  });
});
