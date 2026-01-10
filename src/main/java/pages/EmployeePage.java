package pages;

import org.openqa.selenium.*;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.List;

/**
 * EmployeePage
 *
 * - No assertions inside page
 * - Methods return boolean / string / this
 */
public class EmployeePage extends BasePage {

    // Employee List page anchors
    private final By employeeListHeader = By.xpath("//h5[text()='Employee Information']");

    // Search: Employee Id input
    private final By empIdSearchInput = By.xpath("//label[contains(.,'Employee Id')]/../following-sibling::div//input");

    // Search button on Employee List page
    private final By employeeListSearchButton = By.xpath("//h5[text()='Employee Information']/ancestor::div[contains(@class,'oxd-table-filter')]//button[@type='submit']");

    // Results
    private final By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");
    private final By tableRowCards = By.cssSelector(".oxd-table-body .oxd-table-card");
    private final By noRecordsFoundText = By.xpath("//*[contains(text(),'No Records Found')]");

    // -------- Personal Details fields --------
    private final By personalDetailsHeader = By.xpath("//h6[contains(.,'Personal Details')]");
    private final By firstNameInput = By.name("firstName");
    private final By dobInput = By.xpath("//label[contains(.,'Date of Birth')]/../following-sibling::div//input");

    // Nationality dropdown
    private final By nationalityDropdown = By.xpath("//label[contains(.,'Nationality')]/../following-sibling::div//div[contains(@class,'oxd-select-text')]");

    // Gender radio buttons
    private final By maleRadio = By.xpath("//label[normalize-space()='Male']/span");
    private final By femaleRadio = By.xpath("//label[normalize-space()='Female']/span");

    // Save button inside Personal Details section
    private final By personalDetailsSaveBtn = By.xpath("//button[normalize-space()='Save' and @type='submit'][1]");
    private final By personalDetailsSaveBtnAlt = By.xpath("//*[@id='app']/div[1]/div[2]/div[2]/div/div/div/div[2]/div[1]/form/div[4]/button");

    // Loaders
    private final By formLoader = By.cssSelector("div.oxd-form-loader");
    private final By pageLoader = By.cssSelector("div.oxd-loading-spinner");

    // ✅ Toast (new stable locator)
    private final By toastContainer = By.cssSelector(".oxd-toast-container");
    private final By toastMessageOld = By.xpath("//p[contains(@class,'oxd-text--toast-message')]");

    // We will reuse PIMPage
    private final PIMPage pimPage;

    // Delete Confirmation
    private final By confirmDeleteButton = By.xpath("//button[contains(.,'Yes, Delete')]");
    private final By deleteIconFirstRow = By.cssSelector(".oxd-table-body .oxd-table-card .bi-trash");

    public EmployeePage(WebDriver driver) {
        super(driver);
        this.pimPage = new PIMPage(driver);
    }

    // ==========================================================
    // NAVIGATION METHODS
    // ==========================================================

    public EmployeePage goToPIMModule() {
        navigateToPIM();
        waitForLoaderToDisappear();
        return this;
    }

    public EmployeePage openAddEmployee() {
        pimPage.clickAddEmployeeMenu();
        waitForLoaderToDisappear();
        return this;
    }

    public EmployeePage openEmployeeList() {
        pimPage.clickEmployeeListMenu();
        waitForLoaderToDisappear();
        return this;
    }

    // ==========================================================
    // DATA METHODS
    // ==========================================================

    public String captureGeneratedEmployeeId() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(
                By.xpath("(//input[@class='oxd-input oxd-input--active'])[2]")
        )).getAttribute("value");
    }

    public String getToastMessageText() {
        // Try stable toast container first
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(toastContainer)).getText();
        } catch (Exception ignored) {}

        // fallback old locator
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(toastMessageOld)).getText();
        } catch (Exception e) {
            return "";
        }
    }

    public String tryGetToastMessage() {
        try {
            if (driver.findElements(toastContainer).size() > 0) {
                return driver.findElement(toastContainer).getText();
            }
        } catch (Exception ignored) {}

        try {
            return driver.findElement(toastMessageOld).getText();
        } catch (Exception e) {
            return "";
        }
    }

    public String getFirstNameValue() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(firstNameInput))
                    .getAttribute("value");
        } catch (Exception e) {
            return "";
        }
    }

    public String getDobValue() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(dobInput))
                    .getAttribute("value");
        } catch (Exception e) {
            return "";
        }
    }

    // ==========================================================
    // VALIDATION METHODS
    // ==========================================================

    public boolean isEmployeeFoundInList() {
        try {
            String recordsText = pimPage.getRecordsFoundText();
            return recordsText != null
                    && !recordsText.trim().isEmpty()
                    && !recordsText.toLowerCase().contains("no records");
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isNoRecordsFoundDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(noRecordsFoundText)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isPersonalDetailsPageLoaded() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(personalDetailsHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * ✅ Stable toast wait:
     * waits for toast container and checks the text.
     */
    public boolean waitForToastToContain(String expectedText, int seconds) {
        try {
            WebDriverWait toastWait = new WebDriverWait(driver, Duration.ofSeconds(seconds));

            toastWait.until(ExpectedConditions.visibilityOfElementLocated(toastContainer));

            boolean matched = toastWait.until(d -> {
                String txt = d.findElement(toastContainer).getText();
                System.out.println("DEBUG TOAST TEXT: " + txt);
                return txt.toLowerCase().contains(expectedText.toLowerCase());
            });

            return matched;
        } catch (Exception e) {
            System.out.println("DEBUG: Toast not found or mismatch: " + e.getMessage());
            return false;
        }
    }

    public boolean isRecordFound() {
        try {
            waitForEmployeeListResults();

            if (driver.findElements(noRecordsFoundText).size() > 0) {
                System.out.println("DEBUG: 'No Records Found' displayed");
                return false;
            }

            List<WebElement> recordTexts = driver.findElements(recordsFoundText);
            if (recordTexts.size() > 0) {
                String txt = recordTexts.get(0).getText();
                System.out.println("DEBUG: Records text: " + txt);
                return txt.toLowerCase().contains("record");
            }

            return driver.findElements(tableRowCards).size() > 0;
        } catch (Exception e) {
            return driver.findElements(tableRowCards).size() > 0;
        }
    }

    public boolean verifyEmployeeInTable(String empId, String firstName, String lastName) {
        try {
            wait.until(ExpectedConditions.visibilityOfElementLocated(tableRowCards));
            List<WebElement> rows = driver.findElements(tableRowCards);

            for (WebElement row : rows) {
                String rowText = row.getText().toLowerCase();

                boolean hasEmpId = rowText.contains(empId.toLowerCase());
                boolean hasFirstName = rowText.contains(firstName.toLowerCase());
                boolean hasLastName = rowText.contains(lastName.toLowerCase());

                if (hasEmpId && hasFirstName && hasLastName) {
                    System.out.println("DEBUG: Found matching row: " + row.getText());
                    return true;
                }
            }

            System.out.println("DEBUG: No matching row for empId: " + empId);
            return false;
        } catch (Exception e) {
            System.out.println("DEBUG: verifyEmployeeInTable error: " + e.getMessage());
            return false;
        }
    }

    public boolean isEmployeeStatusActive(String empId) {
        try {
            wait.until(ExpectedConditions.visibilityOfElementLocated(tableRowCards));
            List<WebElement> rows = driver.findElements(tableRowCards);

            for (WebElement row : rows) {
                String rowText = row.getText().toLowerCase();
                if (rowText.contains(empId.toLowerCase())) {
                    return rowText.contains("active");
                }
            }
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isFirstNameValue(String expected) {
        try {
            String actual = wait.until(ExpectedConditions.visibilityOfElementLocated(firstNameInput)).getAttribute("value");
            return actual != null && actual.trim().equalsIgnoreCase(expected.trim());
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isDobValue(String expected) {
        try {
            String actual = wait.until(ExpectedConditions.visibilityOfElementLocated(dobInput)).getAttribute("value");
            return actual != null && actual.trim().equals(expected.trim());
        } catch (Exception e) {
            return false;
        }
    }

    // ==========================================================
    // ACTION METHODS
    // ==========================================================

    public String createEmployeeAndGetEmployeeId(String firstName, String middleName, String lastName) {
        pimPage.enterFirstName(firstName);
        pimPage.enterMiddleName(middleName);
        pimPage.enterLastName(lastName);

        String empId = captureGeneratedEmployeeId();

        pimPage.clickSaveButton();

        try {
            wait.until(ExpectedConditions.visibilityOfElementLocated(personalDetailsHeader));
        } catch (Exception ignored) {}

        waitForLoaderToDisappear();
        return empId;
    }

    public EmployeePage searchEmployeeInListById(String empId) {
        wait.until(ExpectedConditions.visibilityOfElementLocated(employeeListHeader));
        waitForLoaderToDisappear();

        // ✅ close any leftover dropdowns
        closeAnyOpenDropdownOverlay();
        waitForLoaderToDisappear();

        WebElement input = wait.until(ExpectedConditions.presenceOfElementLocated(empIdSearchInput));

        // ✅ scroll into view
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", input);

        // ✅ wait until clickable (prevents intercept issue)
        wait.until(ExpectedConditions.elementToBeClickable(empIdSearchInput));

        // ✅ try normal click, if intercepted then JS click
        try {
            input.click();
        } catch (ElementClickInterceptedException e) {
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", input);
        }

        // ✅ clear existing value
        input.sendKeys(Keys.CONTROL + "a");
        input.sendKeys(Keys.BACK_SPACE);

        // ✅ type employee id
        input.sendKeys(empId);

        // ✅ click Search
        safeClick(employeeListSearchButton);

        waitForEmployeeListResults();
        waitForLoaderToDisappear();
        return this;
    }


    public EmployeePage clickFoundEmployeeRecord(String empId) {
        By empIdCell = By.xpath("//div[contains(@class,'oxd-table-body')]//div[contains(@class,'oxd-table-cell')]/div[normalize-space()='" + empId + "']");
        safeClick(empIdCell);

        wait.until(ExpectedConditions.visibilityOfElementLocated(personalDetailsHeader));
        waitForLoaderToDisappear();
        return this;
    }
    public EmployeePage updatePersonalDetailsDirectly(String newFirstName, String dob, String nationality, String gender) {

        wait.until(ExpectedConditions.visibilityOfElementLocated(personalDetailsHeader));
        waitForLoaderToDisappear();

        // 1) Update First Name
        clickAndClearType(firstNameInput, newFirstName);

        // 2) Update DOB
        clickAndClearType(dobInput, dob);

        // 3) Select Nationality (FIXED)
        selectFromOrangeHRMDropdown(nationalityDropdown, nationality);

        // 4) Select Gender
        if (gender.equalsIgnoreCase("male")) safeClick(maleRadio);
        if (gender.equalsIgnoreCase("female")) safeClick(femaleRadio);

        waitForLoaderToDisappear();

        // 5) Click Save
        safeClick(personalDetailsSaveBtn);

        // 6) Wait for loader + toast
        waitForLoaderToDisappear();
        waitForAnyToast(8);

        return this;
    }


    /**
     * ✅ UPDATED Delete method with stable sync
     */
    public EmployeePage deleteEmployeeFromSearchResults() {
        safeClick(deleteIconFirstRow);

        // confirmation popup button
        safeClick(confirmDeleteButton);

        // Wait for loader + toast (sync)
        waitForLoaderToDisappear();

        // Toast might be: "Successfully Deleted" or just "Success"
        waitForToastToContain("Delete", 8);
        return this;
    }

    public EmployeePage logoutFromApp() {
        logout();
        return this;
    }

    // ==========================================================
    // HELPER METHODS
    // ==========================================================

    private void waitForLoaderToDisappear() {
        try {
            wait.until(ExpectedConditions.invisibilityOfElementLocated(formLoader));
        } catch (Exception ignored) {}
        try {
            wait.until(ExpectedConditions.invisibilityOfElementLocated(pageLoader));
        } catch (Exception ignored) {}
    }

    private void waitForEmployeeListResults() {
        WebDriverWait w = new WebDriverWait(driver, Duration.ofSeconds(12));
        w.until(d ->
                d.findElements(recordsFoundText).size() > 0 ||
                        d.findElements(noRecordsFoundText).size() > 0 ||
                        d.findElements(tableRowCards).size() > 0
        );
    }

    private void safeClick(By locator) {
        waitForLoaderToDisappear();

        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", element);

        waitForLoaderToDisappear();

        try {
            wait.until(ExpectedConditions.elementToBeClickable(locator)).click();
        } catch (ElementClickInterceptedException e) {
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
        }

        waitForLoaderToDisappear();
    }

    private void clickAndClearType(By locator, String value) {
        WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated(locator));
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", el);

        el.click();
        waitForLoaderToDisappear();

        el.sendKeys(Keys.CONTROL + "a");
        el.sendKeys(Keys.BACK_SPACE);
        el.sendKeys(value);
    }
    private void closeAnyOpenDropdownOverlay() {
        try {
            // press ESC to close dropdowns/autocomplete
            driver.findElement(By.tagName("body")).sendKeys(Keys.ESCAPE);
            Thread.sleep(200);
        } catch (Exception ignored) {}

        try {
            // if any dropdown list still visible, click on page background
            List<WebElement> uls = driver.findElements(By.xpath("//ul[contains(@class,'oxd-select-dropdown')]"));
            if (!uls.isEmpty() && uls.get(0).isDisplayed()) {
                driver.findElement(By.tagName("body")).click();
                Thread.sleep(200);
            }
        } catch (Exception ignored) {}
    }

    /**
     * ✅ Correct dropdown selection for OrangeHRM select components
     */
    private void selectFromOrangeHRMDropdown(By dropdownLocator, String optionText) {
        waitForLoaderToDisappear();

        WebElement dropdown = wait.until(ExpectedConditions.elementToBeClickable(dropdownLocator));
        ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block:'center'});", dropdown);

        // Click dropdown
        dropdown.click();

        // Wait dropdown options open
        By optionLocator = By.xpath("//div[@role='option']//span[contains(normalize-space(),'" + optionText + "')]");
        wait.until(ExpectedConditions.visibilityOfElementLocated(optionLocator));

        // Click option
        WebElement option = wait.until(ExpectedConditions.elementToBeClickable(optionLocator));
        option.click();

        waitForLoaderToDisappear();
    }

    /**
     * ✅ Waits for any toast (not strict locator)
     */
    private void waitForAnyToast(int seconds) {
        try {
            WebDriverWait w = new WebDriverWait(driver, Duration.ofSeconds(seconds));

            // OrangeHRM uses toast container / toast content
            By anyToast = By.xpath("//*[contains(@class,'oxd-toast') or contains(@class,'oxd-toast-container')]");

            w.until(ExpectedConditions.visibilityOfElementLocated(anyToast));
            System.out.println("DEBUG: Toast appeared: " + driver.findElement(anyToast).getText());
        } catch (Exception e) {
            System.out.println("DEBUG: Toast not detected (not mandatory): " + e.getMessage());
        }
    }
    public boolean waitUntilNoRecordsFound(int seconds) {
        try {
            WebDriverWait w = new WebDriverWait(driver, Duration.ofSeconds(seconds));

            return w.until(d -> {
                // Case 1: No Records Found text visible
                if (d.findElements(noRecordsFoundText).size() > 0) {
                    return d.findElement(noRecordsFoundText).isDisplayed();
                }

                // Case 2: Table has no rows
                if (d.findElements(tableRowCards).size() == 0) {
                    return true;
                }

                // Case 3: Records text says 0 record(s)
                if (d.findElements(recordsFoundText).size() > 0) {
                    String txt = d.findElement(recordsFoundText).getText().toLowerCase();
                    return txt.contains("0 record");
                }

                return false;
            });

        } catch (Exception e) {
            System.out.println("DEBUG: waitUntilNoRecordsFound failed: " + e.getMessage());
            return false;
        }
    }


}
