import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';

class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('measurements.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);

    return await openDatabase(path, version: 1, onCreate: _createDB);
  }

  Future _createDB(Database db, int version) async {
    await db.execute('''
CREATE TABLE measurements (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  device_id TEXT,
  network_type TEXT,
  rsrp INTEGER,
  sinr INTEGER,
  cell_id INTEGER,
  latitude REAL,
  longitude REAL,
  timestamp TEXT
)
''');
  }

  Future<int> insertMeasurement(Map<String, dynamic> row) async {
    final db = await instance.database;
    return await db.insert('measurements', row);
  }

  Future<List<Map<String, dynamic>>> queryAllMeasurements() async {
    final db = await instance.database;
    return await db.query('measurements');
  }

  Future<int> deleteMeasurement(int id) async {
    final db = await instance.database;
    return await db.delete('measurements', where: 'id = ?', whereArgs: [id]);
  }

  Future<int> clearAll() async {
    final db = await instance.database;
    return await db.delete('measurements');
  }
}
