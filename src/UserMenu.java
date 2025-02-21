package src;

import com.jacob.activeX.ActiveXComponent;
import com.jacob.com.Dispatch;
import com.jacob.com.Variant;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.awt.GridLayout;

import javax.swing.ImageIcon;
import javax.swing.JFrame;
import javax.swing.JLabel;

import org.json.JSONArray;
import org.json.JSONObject;
// import json.JSONArray;

public class UserMenu {
    private ActiveXComponent server;
    private String token;
    private ScheduledExecutorService scheduler;
    private String saveFolder = "out";
    private String cacheFolder = "cache/img";

    public UserMenu(ActiveXComponent server, String token) {
        this.server = server;
        this.token = token;
        this.scheduler = Executors.newScheduledThreadPool(1);
    }

    private void clearConsole() {
        try {
            new ProcessBuilder("cmd", "/c", "cls").inheritIO().start().waitFor();
        } catch (Exception e) {
            System.out.println("Ошибка очистки консоли");
        }
    }

    private void clearFolder(String folderPath) {
        File folder = new File(folderPath);
        if (folder.exists()) {
            for (File file : Objects.requireNonNull(folder.listFiles())) {
                file.delete();
            }
        }
        new File(folderPath).mkdirs();
    }

    private void saveWp(String result, Integer index, boolean isCache) {
        try {
            JSONObject jsonResponse = new JSONObject(result);
            JSONArray wallpapers = jsonResponse.getJSONArray("data");

            if (index == null) {
                for (int i = 0; i < Math.min(10, wallpapers.length()); i++) {
                    JSONObject wpData = wallpapers.getJSONObject(i);
                    String imgUrl = isCache ? wpData.getJSONObject("thumbs").getString("small")
                            : wpData.getString("path");
                    String imgName = String.valueOf(i + 1);
                    downloadWp(imgUrl, imgName, isCache);
                }
            } else {
                JSONObject wpData = wallpapers.getJSONObject(index);
                String imgUrl = isCache ? wpData.getJSONObject("thumbs").getString("small") : wpData.getString("path");
                String imgName = wpData.getString("id");
                downloadWp(imgUrl, imgName, isCache);
            }
        } catch (Exception e) {
            System.out.println("Ошибка при сохранении обоев: " + e.getMessage());
        }
    }

    private void downloadWp(String imgUrl, String imgName, boolean isCache) {
        try (InputStream in = new URL(imgUrl).openStream()) {
            String folder = isCache ? cacheFolder : saveFolder;
            Files.createDirectories(Paths.get(folder));
            Files.copy(in, Paths.get(folder, imgName + ".jpg"), StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException e) {
            System.out.println("Ошибка загрузки изображения: " + e.getMessage());
        }
    }

    public void displayImagesInFolderSingleWindow() {
        File folder = new File(cacheFolder);
        if (!folder.exists() || !folder.isDirectory()) {
            System.out.println("Никаких обоев не было найдено");
            return;
        }

        // Фильтруем файлы по допустимым расширениям
        List<String> validExtensions = Arrays.asList("jpg", "jpeg", "png", "bmp", "gif", "tiff", "webp");
        File[] imageFiles = folder.listFiles((dir, name) -> {
            String lowerCaseName = name.toLowerCase();
            return validExtensions.stream().anyMatch(lowerCaseName::endsWith);
        });

        if (imageFiles == null || imageFiles.length == 0) {
            System.out.println("Никаких обоев не было найдено");
            return;
        }

        int numImages = imageFiles.length;
        int cols = Math.min(4, numImages); // Макс. 4 колонки
        int rows = (numImages + cols - 1) / cols; // Количество строк

        // Создаем окно
        JFrame frame = new JFrame("Обои");
        frame.setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        frame.setLayout(new GridLayout(rows, cols, 10, 10)); // Сетка с отступами

        // Добавляем изображения в окно
        for (File imageFile : imageFiles) {
            ImageIcon icon = new ImageIcon(imageFile.getAbsolutePath());
            JLabel label = new JLabel(imageFile.getName(), icon, JLabel.CENTER);
            label.setVerticalTextPosition(JLabel.BOTTOM);
            label.setHorizontalTextPosition(JLabel.CENTER);
            frame.add(label);
        }

        frame.pack();
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
    }

    public void scheduledWallpaper(int delay, int page) {
        try {
            // Получаем предпочтения пользователя
            String categoriesJson = server.invoke("get_user_preferences", new Variant[]{new Variant(token), new Variant("categories")}).toString();
            List<String> categories = List.of(categoriesJson.split(",")); // Парсим категории

            // Формируем строку категорий "1" / "0"
            String categoriesStr = (categories.contains("General") ? "1" : "0") +
                                   (categories.contains("Anime") ? "1" : "0") +
                                   (categories.contains("People") ? "1" : "0");

            // Разрешения
            String resolutionsJson = server.invoke("get_user_preferences", new Variant[]{new Variant(token), new Variant("resolutions")}).toString();
            String[] resolutionsArray = resolutionsJson.split(",");

            // Теги
            String query = server.invoke("get_user_preferences", new Variant[]{new Variant(token), new Variant("tags")}).toString();

            // Выполняем поиск обоев
            String resultJson = Dispatch.call(server, "search_wallpapers", 
                    token,
                    query,
                    categoriesStr,
                    resolutionsArray,
                    null,
                    page
            ).toString();

            // JSONObject result = new JSONObject(resultJson);
            saveWp(resultJson, null, false);

        } catch (Exception e) {
            System.out.println("Ошибка при выполнении scheduledWallpaper: " + e.getMessage());
        }
    }

    public String inputCategories() {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Нужно ли искать General [Y/other]: ");
        boolean general = scanner.nextLine().trim().equalsIgnoreCase("Y");

        System.out.print("Нужно ли искать Anime [Y/other]: ");
        boolean anime = scanner.nextLine().trim().equalsIgnoreCase("Y");

        System.out.print("Нужно ли искать People [Y/other]: ");
        boolean people = scanner.nextLine().trim().equalsIgnoreCase("Y");

        return (general ? "1" : "0") + (anime ? "1" : "0") + (people ? "1" : "0");
    }

    public List<String> inputResolution() {
        Scanner scanner = new Scanner(System.in);
        List<String> resolutionList = new ArrayList<>();

        System.out.print("Нужно ли определенное разрешение? [Y/other]: ");
        boolean needTo = scanner.nextLine().trim().equalsIgnoreCase("Y");

        while (needTo) {
            System.out.print("Введите разрешение: ");
            resolutionList.add(scanner.nextLine().trim());

            System.out.print("Еще? [Y/other]: ");
            needTo = scanner.nextLine().trim().equalsIgnoreCase("Y");
        }

        return resolutionList.isEmpty() ? null : resolutionList;
    }

    public String inputWpId() {
        Scanner scanner = new Scanner(System.in);
        System.out.print("Есть ли определенный ID? [Y/other]: ");
        boolean needTo = scanner.nextLine().trim().equalsIgnoreCase("Y");

        if (needTo) {
            System.out.print("Введите определенный ID: ");
            return scanner.nextLine().trim();
        }
        return null;
    }

    public String wallpaperSearchMenu() {
        String result = null;
        Scanner scanner = new Scanner(System.in);
        while (true) {
            clearConsole();
            System.out.println("__Поиск обоев__");
            System.out.println("1) Поиск обоев");
            System.out.println("2) Случайные обои");
            System.out.println("3) Обои дня");
            System.out.println("4) Обои по рассылке");
            System.out.println("5) Вернуться");
            System.out.print("Выберите действие: ");
            String choice = scanner.nextLine();

            switch (choice) {
                case "1":
                    try {
                        System.out.print("Введите поисковый запрос: ");
                        String query = scanner.nextLine();
                        String categories = inputCategories();
                        List<String> resolutions = inputResolution();
                        String wallpaperId = inputWpId();
                        System.out.print("Введите номер страницы: ");
                        int page = Integer.parseInt(scanner.nextLine().trim());

                        Variant resultVariant = Dispatch.call(server, "search_wallpapers", 
                                token,
                                query,
                                categories,
                                resolutions,
                                wallpaperId,
                                page
                        );
                        result = resultVariant.toString();
                        
                        clearFolder(cacheFolder);
                        saveWp(result, null, true);
                        displayImagesInFolderSingleWindow();
                        System.out.print("Введите номер обоев для сохранения через пробел: ");
                        String[] wpIds = scanner.nextLine().split(" ");

                        for (String wpId : wpIds) {
                            saveWp(result, Integer.parseInt(wpId) - 1, false);
                        }
                        break;
                    } catch (Exception e) {
                        System.out.println("Что-то пошло не так. Попробуйте снова");
                    }
                    break;
                case "2":
                    result = server.invoke("random_wallpaper", token).toString();
                    clearFolder(cacheFolder);
                    saveWp(result, 0, true);
                    displayImagesInFolderSingleWindow();
                    saveWp(result, 0, false);
                    break;
                case "3":
                    result = server.invoke("wallpaper_of_day", token).toString();
                    clearFolder(cacheFolder);
                    saveWp(result, 0, true);
                    displayImagesInFolderSingleWindow();
                    saveWp(result, 0, false);
                    break;
                case "4":
                    try {
                        System.out.print("Введите время рассылки новых обоев в секундах: ");
                        int delay = Integer.parseInt(scanner.nextLine());

                        Timer timer = new Timer();
                        timer.scheduleAtFixedRate(new TimerTask() {
                            private int page = 1;
                
                            @Override
                            public void run() {
                                scheduledWallpaper(delay, page);
                                page++; // Увеличиваем страницу при каждом запуске
                            }
                        }, 0, delay * 1000);
                        System.out.println("Рассылка настроена. Нажмите Enter, чтобы продолжить.");
                        scanner.nextLine();
                    } catch (Exception e) {
                        System.out.println("Неверный ввод. Нажмите Enter, чтобы выйти.");
                        scanner.nextLine();
                    }
                    break;
                case "5":
                    clearConsole();
                    System.out.println("Возврат...");
                    return result;
                default:
                    System.out.println("Неверный выбор. Нажмите Enter, чтобы попробовать снова.");
                    scanner.nextLine();
            }
        }
    }

    public void userConfigMenu() {
        Scanner scanner = new Scanner(System.in);

        while (true) {
            clearConsole();
            System.out.println("__Меню пользователя__");
            System.out.println("1) Добавить предпочтение при рассылке");
            System.out.println("2) Удалить предпочтение при рассылке");
            System.out.println("3) Указать путь сохранения обоев");
            System.out.println("4) Выйти");
            System.out.print("Выберите действие: ");

            String choice = scanner.nextLine().trim();

            switch (choice) {
                case "1":
                    Preference pref = choosePref(scanner);
                    if (pref == null) continue;
                    try {
                        Dispatch.call(server, "add_user_config", token, pref.type, pref.value);
                    } catch (Exception e) {
                        System.out.println("Произошла ошибка. Возможно, значение уже было добавлено.");
                        waitForEnter(scanner);
                    }
                    break;

                case "2":
                    Preference prefToRemove = choosePrefForRemove(scanner);
                    if (prefToRemove == null) continue;
                    try {
                        Dispatch.call(server, "remove_user_config", token, prefToRemove.type, prefToRemove.value);
                    } catch (Exception e) {
                        System.out.println("Произошла ошибка.");
                        waitForEnter(scanner);
                    }
                    break;

                case "3":
                    System.out.println("Текущий путь для сохранения обоев: " + saveFolder);
                    System.out.print("Введите путь для сохранения: ");
                    String savePath = scanner.nextLine().trim();

                    try {
                        Path path = Path.of(savePath);
                        Files.createDirectories(path);
                        if (Files.isDirectory(path)) {
                            saveFolder = savePath;
                            System.out.println("Путь успешно сохранен.");
                        } else {
                            System.out.println("Некорректный путь.");
                        }
                    } catch (Exception e) {
                        System.out.println("Некорректный путь.");
                    }
                    waitForEnter(scanner);
                    break;

                case "4":
                    clearConsole();
                    System.out.println("Выход из программы...");
                    return;

                default:
                    System.out.println("Неверный выбор.");
                    waitForEnter(scanner);
            }
        }
    }

    private Preference choosePrefForRemove(Scanner scanner) {
        System.out.println("1) Категории");
        System.out.println("2) Тэг");
        System.out.println("3) Разрешение");
        System.out.print("Выберите тип настройки: ");
        String choice = scanner.nextLine().trim();

        String type;
        switch (choice) {
            case "1":
                type = "categories";
                break;
            case "2":
                type = "tags";
                break;
            case "3":
                type = "resolutions";
                break;
            default:
                System.out.println("Некорректный ввод.");
                waitForEnter(scanner);
                return null;
        }

        String namesJson = Dispatch.call(server, "get_user_preferences", token, type).toString();
        List<String> names = List.of(namesJson.split(" "));
        System.out.println("Выберите среди: " + String.join(" ", names));

        System.out.print("Введите значение: ");
        String pref = scanner.nextLine().trim();

        if (!pref.isEmpty() && names.contains(pref)) {
            System.out.println("Настройка введена.");
            return new Preference(type, pref);
        } else {
            System.out.println("Некорректный ввод.");
            waitForEnter(scanner);
            return null;
        }
    }

    private Preference choosePref(Scanner scanner) {
        System.out.println("1) Категории");
        System.out.println("2) Тэг");
        System.out.println("3) Разрешение");
        System.out.print("Выберите тип настройки: ");
        String choice = scanner.nextLine().trim();

        String type;
        switch (choice) {
            case "1":
                type = "categories";
                break;
            case "2":
                type = "tags";
                break;
            case "3":
                type = "resolutions";
                break;
            default:
                System.out.println("Некорректный ввод.");
                waitForEnter(scanner);
                return null;
        }

        String namesJson = Dispatch.call(server, "get_all_preferences", type).toString();
        List<String> names = List.of(namesJson.split(" "));
        System.out.println("Выберите среди: " + String.join(" ", names));

        System.out.print("Введите значение: ");
        String pref = scanner.nextLine().trim();

        if (!pref.isEmpty() && names.contains(pref)) {
            System.out.println("Настройка введена.");
            return new Preference(type, pref);
        } else {
            System.out.println("Некорректный ввод.");
            waitForEnter(scanner);
            return null;
        }
    }

    private void waitForEnter(Scanner scanner) {
        System.out.println("Нажмите Enter, чтобы продолжить...");
        scanner.nextLine();
    }

    private static class Preference {
        String type;
        String value;

        public Preference(String type, String value) {
            this.type = type;
            this.value = value;
        }
    }

    public void userMenu() {
        Scanner scanner = new Scanner(System.in);
        while (true) {
            clearConsole();
            System.out.println("__Меню пользователя__");
            System.out.println("1) Найти обои");
            System.out.println("2) Настройки профиля");
            System.out.println("3) Выйти");
            System.out.print("Выберите действие: ");
            String choice = scanner.nextLine();

            switch (choice) {
                case "1":
                    wallpaperSearchMenu();
                    break;
                case "2":
                    userConfigMenu();
                    break;
                case "3":
                    System.out.println("Выход из программы...");
                    return;
                default:
                    System.out.println("Неверный выбор. Попробуйте снова.");
            }
        }
    }
}
