package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class PIMPage extends BasePage {

    // Locators
    private By pimHeader = By.xpath("//h6[text()='PIM']");
    private By addEmployeeMenu = By.xpath("//a[text()='Add Employee']");
    private By employeeListMenu = By.xpath("//a[text()='Employee List']");
    private By firstNameField = By.name("firstName");
    private By middleNameField = By.name("middleName");
    private By lastNameField = By.name("lastName");
    private By employeeIdField = By.xpath("(//input[@class='oxd-input oxd-input--active'])[2]");
    private By saveButton = By.xpath("//button[@type='submit']");
    private By searchEmployeeIdField = By.xpath("(//input[@class='oxd-input oxd-input--active'])[2]");
    private By searchButton = By.xpath("//button[@type='submit']");
    private By resetButton = By.xpath("//button[normalize-space()='Reset']");
    private By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");
    private By createLoginToggle = By.xpath("//span[@class='oxd-switch-input oxd-switch-input--active --label-right']");
    private By usernameField = By.xpath("(//input[@class='oxd-input oxd-input--active'])[3]");
    private By passwordField = By.xpath("(//input[@type='password'])[1]");
    private By confirmPasswordField = By.xpath("(//input[@type='password'])[2]");
    private By successMessage = By.xpath("//p[contains(@class,'oxd-text--toast-message')]");

    // Constructor
    public PIMPage(WebDriver driver) {
        super(driver);
    }

    // COMMON METHOD: Used across multiple test classes
    public boolean isPageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(pimHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used across multiple test classes
    public String getPageTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(pimHeader)).getText();
    }

    public void clickAddEmployeeMenu() {
        WebElement addEmpMenu = wait.until(ExpectedConditions.elementToBeClickable(addEmployeeMenu));
        addEmpMenu.click();
    }

    public void clickEmployeeListMenu() {
        WebElement empListMenu = wait.until(ExpectedConditions.elementToBeClickable(employeeListMenu));
        empListMenu.click();
    }

    // COMMON METHOD: Used in PIM and Admin tests
    public void enterFirstName(String firstName) {
        WebElement firstNameElem = wait.until(ExpectedConditions.visibilityOfElementLocated(firstNameField));
        firstNameElem.clear();
        firstNameElem.sendKeys(firstName);
    }

    // COMMON METHOD: Used in PIM and Admin tests
    public void enterMiddleName(String middleName) {
        WebElement middleNameElem = wait.until(ExpectedConditions.visibilityOfElementLocated(middleNameField));
        middleNameElem.clear();
        middleNameElem.sendKeys(middleName);
    }

    // COMMON METHOD: Used in PIM and Admin tests
    public void enterLastName(String lastName) {
        WebElement lastNameElem = wait.until(ExpectedConditions.visibilityOfElementLocated(lastNameField));
        lastNameElem.clear();
        lastNameElem.sendKeys(lastName);
    }

    public void enterEmployeeId(String employeeId) {
        WebElement empIdElem = wait.until(ExpectedConditions.visibilityOfElementLocated(employeeIdField));
        empIdElem.clear();
        empIdElem.sendKeys(employeeId);
    }

    // COMMON METHOD: Used across multiple modules
    public void clickSaveButton() {
        WebElement saveBtn = wait.until(ExpectedConditions.elementToBeClickable(saveButton));
        saveBtn.click();
    }

    public void enableCreateLoginDetails() {
        try {
            WebElement toggle = wait.until(ExpectedConditions.elementToBeClickable(createLoginToggle));
            toggle.click();
        } catch (Exception e) {
            System.out.println("Create login toggle not found or already enabled");
        }
    }

    // COMMON METHOD: Used in PIM and Admin tests
    public void enterUsername(String username) {
        WebElement usernameElem = wait.until(ExpectedConditions.visibilityOfElementLocated(usernameField));
        usernameElem.clear();
        usernameElem.sendKeys(username);
    }

    // COMMON METHOD: Used in PIM and Admin tests
    public void enterPassword(String password) {
        WebElement passwordElem = wait.until(ExpectedConditions.visibilityOfElementLocated(passwordField));
        passwordElem.clear();
        passwordElem.sendKeys(password);
    }

    public void enterConfirmPassword(String confirmPassword) {
        WebElement confirmPwdElem = wait.until(ExpectedConditions.visibilityOfElementLocated(confirmPasswordField));
        confirmPwdElem.clear();
        confirmPwdElem.sendKeys(confirmPassword);
    }

    public void enterSearchEmployeeId(String employeeId) {
        WebElement searchField = wait.until(ExpectedConditions.visibilityOfElementLocated(searchEmployeeIdField));
        searchField.clear();
        searchField.sendKeys(employeeId);
    }

    // COMMON METHOD: Used across multiple test classes
    public void clickSearchButton() {
        WebElement searchBtn = wait.until(ExpectedConditions.elementToBeClickable(searchButton));
        searchBtn.click();
    }

    // COMMON METHOD: Used across multiple test classes
    public void clickResetButton() {
        WebElement resetBtn = wait.until(ExpectedConditions.elementToBeClickable(resetButton));
        resetBtn.click();
    }

    // COMMON METHOD: Shared with Leave, Time, Admin, Recruitment tests
    public String getRecordsFoundText() {
        try {
            Thread.sleep(2000); // Wait for records to load
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recordsFoundText)).getText();
    }

    public boolean isSuccessMessageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(successMessage)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public String getSuccessMessage() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(successMessage)).getText();
    }

    // Combined method for adding employee
    public void addEmployee(String firstName, String middleName, String lastName, String employeeId) {
        clickAddEmployeeMenu();
        enterFirstName(firstName);
        enterMiddleName(middleName);
        enterLastName(lastName);
        enterEmployeeId(employeeId);
        clickSaveButton();
    }

    // Combined method for adding employee with login
    public void addEmployeeWithLogin(String firstName, String middleName, String lastName,
                                     String employeeId, String username, String password) {
        clickAddEmployeeMenu();
        enterFirstName(firstName);
        enterMiddleName(middleName);
        enterLastName(lastName);
        enterEmployeeId(employeeId);
        enableCreateLoginDetails();
        enterUsername(username);
        enterPassword(password);
        enterConfirmPassword(password);
        clickSaveButton();
    }

    // Combined method for searching employee
    public void searchEmployee(String employeeId) {
        clickEmployeeListMenu();
        enterSearchEmployeeId(employeeId);
        clickSearchButton();
    }
}