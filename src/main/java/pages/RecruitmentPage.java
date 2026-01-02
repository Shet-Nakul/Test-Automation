package pages;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class RecruitmentPage extends BasePage {

    // Locators
    private By recruitmentHeader = By.xpath("//h6[text()='Recruitment']");
    private By addButton = By.xpath("//button[normalize-space()='Add']");
    private By candidatesMenu = By.xpath("//a[text()='Candidates']");
    private By vacanciesMenu = By.xpath("//a[text()='Vacancies']");
    private By candidateNameField = By.xpath("(//input[@placeholder='Type for hints...'])[1]");
    private By fromDateField = By.xpath("(//input[@placeholder='yyyy-dd-mm'])[1]");
    private By toDateField = By.xpath("(//input[@placeholder='yyyy-dd-mm'])[2]");
    private By searchButton = By.xpath("//button[@type='submit']");
    private By resetButton = By.xpath("//button[normalize-space()='Reset']");
    private By jobTitleDropdown = By.xpath("(//div[@class='oxd-select-text-input'])[1]");
    private By recordsFoundText = By.xpath("//span[contains(@class,'oxd-text--span')]");
    private By vacancyDropdown = By.xpath("(//div[@class='oxd-select-text-input'])[2]");

    // Constructor
    public RecruitmentPage(WebDriver driver) {
        super(driver);
    }

    // COMMON METHOD: Used across multiple test classes
    public boolean isPageDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(recruitmentHeader)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used across multiple test classes
    public String getPageTitle() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recruitmentHeader)).getText();
    }

    // COMMON METHOD: Shared with AdminPage
    public void clickAddButton() {
        WebElement addBtn = wait.until(ExpectedConditions.elementToBeClickable(addButton));
        addBtn.click();
    }

    public void clickCandidatesMenu() {
        WebElement candidatesMenuItem = wait.until(ExpectedConditions.elementToBeClickable(candidatesMenu));
        candidatesMenuItem.click();
    }

    public void clickVacanciesMenu() {
        WebElement vacanciesMenuItem = wait.until(ExpectedConditions.elementToBeClickable(vacanciesMenu));
        vacanciesMenuItem.click();
    }

    public void enterCandidateName(String name) {
        WebElement nameField = wait.until(ExpectedConditions.visibilityOfElementLocated(candidateNameField));
        nameField.clear();
        nameField.sendKeys(name);
    }

    // COMMON METHOD: Shared with LeavePage and TimePage
    public void enterFromDate(String date) {
        WebElement fromDate = wait.until(ExpectedConditions.visibilityOfElementLocated(fromDateField));
        fromDate.clear();
        fromDate.sendKeys(date);
    }

    // COMMON METHOD: Shared with LeavePage and TimePage
    public void enterToDate(String date) {
        WebElement toDate = wait.until(ExpectedConditions.visibilityOfElementLocated(toDateField));
        toDate.clear();
        toDate.sendKeys(date);
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

    public void clickJobTitleDropdown() {
        WebElement dropdown = wait.until(ExpectedConditions.elementToBeClickable(jobTitleDropdown));
        dropdown.click();
    }

    public void clickVacancyDropdown() {
        WebElement dropdown = wait.until(ExpectedConditions.elementToBeClickable(vacancyDropdown));
        dropdown.click();
    }

    // COMMON METHOD: Shared with LeavePage, TimePage, and AdminPage
    public String getRecordsFoundText() {
        try {
            Thread.sleep(2000); // Wait for records to load
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        return wait.until(ExpectedConditions.visibilityOfElementLocated(recordsFoundText)).getText();
    }

    // COMMON METHOD: Shared with AdminPage
    public boolean isAddButtonDisplayed() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(addButton)).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public boolean isCandidatesMenuDisplayed() {
        try {
            return driver.findElement(candidatesMenu).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    // COMMON METHOD: Used for date range search in multiple modules
    public void searchByDateRange(String fromDate, String toDate) {
        enterFromDate(fromDate);
        enterToDate(toDate);
        clickSearchButton();
    }

    // Method combining multiple common methods
    public void searchCandidate(String candidateName, String fromDate, String toDate) {
        enterCandidateName(candidateName);
        enterFromDate(fromDate);
        enterToDate(toDate);
        clickSearchButton();
    }
}