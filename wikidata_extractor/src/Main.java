import java.io.File;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

import org.wikidata.wdtk.datamodel.interfaces.EntityDocumentProcessor;
import org.wikidata.wdtk.datamodel.interfaces.EntityIdValue;
import org.wikidata.wdtk.datamodel.interfaces.ItemDocument;
import org.wikidata.wdtk.datamodel.interfaces.MonolingualTextValue;
import org.wikidata.wdtk.datamodel.interfaces.PropertyDocument;
import org.wikidata.wdtk.datamodel.interfaces.StatementGroup;
import org.wikidata.wdtk.dumpfiles.DumpContentType;
import org.wikidata.wdtk.dumpfiles.DumpProcessingController;
import org.wikidata.wdtk.dumpfiles.MwDumpFile;

public class Main implements EntityDocumentProcessor {
	final static boolean ONLY_CURRENT_REVISIONS = true;
	final static boolean OFFLINE_MODE = false;
	final static int TIMEOUT_SEC = 0;

	final static String DATABASE_LOCATION = "wikidata.db";
	final static int BATCH_SIZE = 10000;

	Connection con = null;
	PreparedStatement meaningStmt = null;
	Integer counter = 0;
	Integer batchCounter = 0;

	public static void main(String[] args) {
		Main mainObject = new Main();
		try {
			mainObject.initDb();
			System.out.println("Initialization finished!");
		} catch (Exception e) {
			e.printStackTrace();
		}
		mainObject.processDump();

		try {
			mainObject.createIndex();
			mainObject.closeConnection();
		} catch (SQLException e) {
			e.printStackTrace();
		}
	}

	@Override
	public void processItemDocument(ItemDocument itemDocument) {
		counter++;
		if (counter % 10000 == 0) {
			System.out.println("Proccessed " + counter + " Entities");
		}
		List<String> classIds = new ArrayList<String>();
		List<String> terms = new ArrayList<String>();
		for (StatementGroup stmtGr : itemDocument.getStatementGroups()) {
			if (stmtGr.getProperty().getId().equals("P31")) {
				for (org.wikidata.wdtk.datamodel.interfaces.Statement stmt : stmtGr
						.getStatements()) {
					EntityIdValue value = (EntityIdValue) stmt.getValue();
					if (value != null) {
						classIds.add(value.getId());
					}
				}
			}
		}
		if (classIds.size() == 0) {
			return;
		}
		MonolingualTextValue label = itemDocument.getLabels().get("en");
		if (label != null) {
			terms.add(label.getText().toLowerCase());
		}
		if (terms.size() == 0) {
			return;
		}
		List<MonolingualTextValue> aliases = itemDocument.getAliases()
				.get("en");
		if (aliases != null) {
			for (MonolingualTextValue alias : aliases) {
				terms.add(alias.getText().toLowerCase());
			}
		}

		try {
			for (String classId : classIds) {
				for (String term : terms) {
					this.insertMeaningIntoBatch(term, classId);
				}
			}
		} catch (SQLException e) {
			e.printStackTrace();
		}

	}

	@Override
	public void processPropertyDocument(PropertyDocument propertyDocument) {
		counter++;
		if (counter % 10000 == 0) {
			System.out.println("Proccessed " + counter + " Entities");
		}

	}

	public void insertMeaningIntoBatch(String term, String classId)
			throws SQLException {
		meaningStmt.setString(1, term);
		meaningStmt.setString(2, classId);
		meaningStmt.addBatch();
		batchCounter++;
		if (batchCounter >= BATCH_SIZE) {
			meaningStmt.executeBatch();
			con.commit();
			batchCounter = 0;
		}
	}

	public void createIndex() throws SQLException{
		String query = "CREATE INDEX terms_index ON Meanings (Term)";
		java.sql.Statement stmt = con.createStatement();
		stmt.execute(query);
		stmt.close();
		con.commit();
	}

	/**
	 * Initiates the dump processing.
	 */
	public void processDump() {

		// Controller object for processing dumps:
		DumpProcessingController dumpProcessingController = new DumpProcessingController(
				"wikidatawiki");
		dumpProcessingController.setOfflineMode(OFFLINE_MODE);

		dumpProcessingController.registerEntityDocumentProcessor(this, null,
				ONLY_CURRENT_REVISIONS);

		MwDumpFile dumpFile = null;
		// Start processing (may trigger downloads where needed):
		dumpFile = dumpProcessingController
				.getMostRecentDump(DumpContentType.JSON);
		if (dumpFile != null) {
			dumpProcessingController.processDump(dumpFile);
		}

	}

	public void initDb() throws ClassNotFoundException, SQLException {
		// remove old database
		File databaseFile = new File(DATABASE_LOCATION);
		if (databaseFile.exists()) {
			databaseFile.delete();
		}

		java.sql.Statement stmt = null;
		Class.forName("org.sqlite.JDBC");
		con = DriverManager.getConnection("jdbc:sqlite:" + DATABASE_LOCATION);
		con.setAutoCommit(false);
		stmt = con.createStatement();
		String query = "CREATE TABLE Meanings (Id INTEGER PRIMARY KEY AUTOINCREMENT, Term TEXT, ClassId TEXT)";
		stmt.executeUpdate(query);
		stmt.close();
		meaningStmt = con
				.prepareStatement("INSERT INTO Meanings (Term, ClassId) VALUES (?, ?)");
	}

	public void closeConnection() throws SQLException {
		con.close();
	}

}
