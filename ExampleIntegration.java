import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;

public class ExampleIntegration {
  public static void main(String args[]) {
		System.out.println("Starting");

    try {
      ProcessBuilder pb = new ProcessBuilder();

      pb.command(
        "/usr/local/opt/python36/bin/python3.6",
        "app.py",
        "--debug",
        "--simulate-tobii"
      );

      Process process = pb.start();

			// blocked :(
      BufferedReader outputReader = new BufferedReader(new InputStreamReader(process.getInputStream()));
      BufferedReader errorReader = new BufferedReader(new InputStreamReader(process.getErrorStream()));

      String line;
      while ((line = outputReader.readLine()) != null) {
          System.out.println("Output: " + line);
      }

      while ((line = errorReader.readLine()) != null) {
          System.out.println("Error: " + line);
      }

      int exitCode = process.waitFor();
      System.out.println("\nExited with error code : " + exitCode);
    } catch (IOException e) {
      e.printStackTrace();
    } catch (InterruptedException e) {
      e.printStackTrace();
    }
	}
}
