package src;
import com.jacob.activeX.ActiveXComponent;
import com.jacob.com.Variant;
import com.jacob.com.Dispatch;
import java.util.Scanner;

   
public class GuestMenu {
  private ActiveXComponent server;
  
  public GuestMenu(ActiveXComponent serverObj) {
      this.server = serverObj;
  }
  
  public String registerMenu() {
      Scanner scanner = new Scanner(System.in);
      String token = null;
      
      while (true) {
          clearConsole();
          System.out.println("__Главное меню__");
          System.out.println("1) Войти в систему");
          System.out.println("2) Зарегистрироваться");
          System.out.println("3) Выйти");
          System.out.print("Выберите действие: ");
          
          String choice = scanner.nextLine();
          
          switch (choice) {
              case "1":
                  System.out.print("Введите имя пользователя: ");
                  String username = scanner.nextLine();
                  System.out.print("Введите пароль: ");
                  String password = scanner.nextLine();
                  
                  token = Dispatch.call(server, "login", username, password).toString();
                  
                  if (token.equals("null")) {
                      System.out.println("Неверное имя пользователя или пароль");
                      System.out.println("Нажмите любую клавишу, чтобы продолжить");
                      scanner.nextLine();
                  }
                  break;
              
              case "2":
                  System.out.print("Введите имя пользователя: ");
                  username = scanner.nextLine();
                  System.out.print("Введите пароль: ");
                  password = scanner.nextLine();
                  
                  token = Dispatch.call(server, "register", new Variant(username), new Variant(password)).toString();
                  
                  if (token.equals("null")) {
                      System.out.println("Такой пользователь уже существует. Поменяйте имя или войдите.");
                      System.out.println("Нажмите любую клавишу, чтобы продолжить");
                      scanner.nextLine();
                  }
                  break;
              
              case "3":
                  clearConsole();
                  System.out.println("Выход из программы...");
                  return null;
              
              default:
                  System.out.println("Неверный выбор. Нажмите Enter, чтобы попробовать снова.");
                  scanner.nextLine();
          }
          
          if (token != null && !token.equals("null")) {
              break;
          }
      }
      
      return token;
  }
  
  private void clearConsole() {
      try {
          new ProcessBuilder("cmd", "/c", "cls").inheritIO().start().waitFor();
      } catch (Exception e) {
          System.out.println("Ошибка очистки консоли");
      }
  }
}


