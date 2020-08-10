/**
 * POC for testing a replica
 */

import org.junit.Before;
import org.junit.Test;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import static org.junit.Assert.assertEquals;

public class ReplicaTest extends TestUtility {
  private Connection mainConnection;
  private Connection replicaConnection;

  @Before
  public void setup() {
    try {
      mainConnection = makeDefaultConnection();
      mainConnection.setAutoCommit(true);
      replicaConnection = makeConnection("localhost", 15722, "terrier");
      replicaConnection.setAutoCommit(true);
    } catch (SQLException e) {
      DumpSQLException(e);
    }
  }

  /**
   * POC test that sends a query to primary and then replica instance
   */
  @Test
  public void testReplica() throws SQLException {
    PreparedStatement mainPs = mainConnection.prepareStatement("SELECT 1;");
    ResultSet mainRs = mainPs.executeQuery();
    mainRs.next();
    assertEquals(1, mainRs.getInt(1));

    PreparedStatement replicaPs = replicaConnection.prepareStatement("SELECT 2;");
    ResultSet replicaRs = replicaPs.executeQuery();
    replicaRs.next();
    assertEquals(2, replicaRs.getInt(1));
  }
}
