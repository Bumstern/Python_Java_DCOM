package src;
import com.jacob.activeX.ActiveXComponent;


public class Main {
    public static void main(String[] args) {
        try {
            ActiveXComponent comObject = new ActiveXComponent("WallpaperDCOM.Server");
            GuestMenu guest_menu = new GuestMenu(comObject);
            
            String token = guest_menu.registerMenu();
            if (token == null) {
                return;
            }

            UserMenu user_menu = new UserMenu(comObject, token);
            user_menu.userMenu();

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
